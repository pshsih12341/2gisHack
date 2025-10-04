"""Map Assistant implementation using LangChain + Groq (ChatGroq) with 2GIS API integration.

Features:
 - Natural language processing for route planning requests
 - Integration with 2GIS Places API and Geocoder API
 - Route parsing and waypoint extraction
 - Friendly response generation with route suggestions
 - Persistent chat history for context

Dependencies (add to requirements):
	groq
	langchain
	langchain-groq (or langchain>=0.2.0 that bundles provider)
	requests
	aiohttp

Environment:
	GROQ_API_KEY must be set (or passed explicitly) for the model to work.
	DGIS_API_KEY must be set for 2GIS API access.

Example:
	from chatbot import MapAssistant
	assistant = MapAssistant()
	response = assistant.process_route_request("Хочу построить маршрут от Красной площади до Тверской, по дороге зайти в кафе")
	print(response['points'])  # Array of route points
	print(response['text'])   # Friendly response text
"""

from __future__ import annotations

import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Generator, Iterable, List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

try:
	from langchain_groq import ChatGroq  # type: ignore
except ImportError as e:  # pragma: no cover - clear guidance to user
	raise ImportError(
		"langchain_groq is required. Install with: pip install langchain-groq groq langchain"
	) from e

from langchain.schema import (
	HumanMessage,
	AIMessage,
	SystemMessage,
	BaseMessage,
)


DEFAULT_MODEL = "qwen/qwen3-32b"  # Change if you prefer qwen/qwen3-32b, etc.

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('map_assistant.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('MapAssistant')


@dataclass
class RoutePoint:
	"""Represents a point in a route with coordinates and metadata."""
	name: str
	latitude: float
	longitude: float
	point_type: str  # 'start', 'end', 'waypoint', 'poi'
	description: Optional[str] = None
	address: Optional[str] = None


@dataclass
class RouteResponse:
	"""Response from map assistant containing route points and friendly text."""
	points: List[RoutePoint]
	text: str
	success: bool
	error_message: Optional[str] = None


@dataclass
class RouteSegment:
	"""Represents a segment of a route."""
	segment_type: str  # walkway, passage, taxi
	distance: int  # meters
	duration: int  # seconds
	transport_type: Optional[str] = None  # bus, metro, taxi, etc.
	route_name: Optional[str] = None  # bus number, metro line
	description: Optional[str] = None
	waypoints: List[RoutePoint] = None

@dataclass
class Route:
	"""Represents a complete route with segments."""
	route_id: str
	total_distance: int  # meters
	total_duration: int  # seconds
	transfer_count: int
	transport_types: List[str]
	segments: List[RouteSegment]
	summary: str
	raw_data: Optional[Dict[str, Any]] = None  # Raw data from 2GIS API

@dataclass
class EnhancedRouteResponse:
	"""Enhanced response containing route points, routes and friendly text."""
	points: List[RoutePoint]
	routes: Optional[List[Route]] = None
	text: str = ""
	success: bool = True
	error_message: Optional[str] = None


class LangChainGroqChatbot:
	"""Simple chat assistant backed by Groq via LangChain.

	Parameters
	----------
	system_prompt: str
		Initial system instruction (can be changed later via set_system_prompt).
	api_key: Optional[str]
		GROQ API key. If omitted, GROQ_API_KEY env var is used.
	model: str
		Groq model name.
	temperature: float
		Sampling temperature.
	max_tokens: Optional[int]
		Optional response token cap.
	timeout: Optional[float]
		Optional request timeout (seconds).
	extra_llm_kwargs: Dict[str, Any]
		Additional kwargs forwarded to ChatGroq.
	"""

	def __init__(
		self,
		system_prompt: str,
		api_key: Optional[str] = None,
		model: str = DEFAULT_MODEL,
		temperature: float = 0.7,
		max_tokens: Optional[int] = None,
		timeout: Optional[float] = None,
		**extra_llm_kwargs: Any,
	) -> None:
		self._system_prompt = system_prompt
		self._history: List[BaseMessage] = []  # Alternating Human / AI messages
		key = api_key or os.getenv("GROQ_API_KEY")
		if not key:
			raise ValueError(
				"GROQ_API_KEY is not set. Provide api_key param or export environment variable."
			)

		llm_params = {
			"model": model,
			"temperature": temperature,
		}
		if max_tokens is not None:
			llm_params["max_tokens"] = max_tokens
		if timeout is not None:
			llm_params["timeout"] = timeout
		llm_params.update(extra_llm_kwargs)

		# ChatGroq follows the langchain BaseChatModel interface.
		self._llm = ChatGroq(api_key=key, **llm_params)

	# ------------------------------------------------------------------
	# Public API
	# ------------------------------------------------------------------
	@property
	def system_prompt(self) -> str:
		return self._system_prompt

	def set_system_prompt(self, prompt: str) -> None:
		"""Update system instructions for future turns."""
		self._system_prompt = prompt

	def ask(self, question: str) -> str:
		"""Send a user question, update history, and return assistant answer."""
		messages = self._build_messages(question)
		ai_message: AIMessage = self._llm.invoke(messages)  # type: ignore
		# Persist last human + AI messages to history
		self._history.append(HumanMessage(content=question))
		self._history.append(ai_message)
		return ai_message.content

	def ask_stream(self, question: str) -> Generator[str, None, None]:
		"""Stream answer tokens; updates history after completion.

		Yields incremental text chunks (may be empty for some events).
		"""
		messages = self._build_messages(question)
		assembled = []
		for chunk in self._llm.stream(messages):  # type: ignore
			text = getattr(chunk, "content", None)
			if text:
				assembled.append(text)
				yield text
		# Store compiled answer in history
		full_answer = "".join(assembled)
		self._history.append(HumanMessage(content=question))
		self._history.append(AIMessage(content=full_answer))

	def get_history(self) -> List[Dict[str, str]]:
		"""Return chat history as list of dicts: {role, content}."""
		out: List[Dict[str, str]] = []
		for msg in self._history:
			role = (
				"user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else "system"
			)
			out.append({"role": role, "content": msg.content})
		return out

	def save_history_json(self, file_path: str, extra: Optional[Dict[str, Any]] = None) -> None:
		"""Persist full conversation history to JSON file.

		Structure:
		{
		  "system_prompt": str,
		  "created_at": iso8601,
		  "messages": [ {role, content}, ... ],
		  "extra": {...}  # optional metadata
		}
		"""
		payload = {
			"system_prompt": self._system_prompt,
			"created_at": datetime.utcnow().isoformat() + "Z",
			"messages": self.get_history(),
		}
		if extra:
			payload["extra"] = extra
		os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
		with open(file_path, "w", encoding="utf-8") as f:
			json.dump(payload, f, ensure_ascii=False, indent=2)

	def reset_history(self) -> None:
		"""Clear conversation history (system prompt remains)."""
		self._history.clear()

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------
	def _build_messages(self, question: str) -> List[BaseMessage]:
		messages: List[BaseMessage] = [SystemMessage(content=self._system_prompt)]
		messages.extend(self._history)
		messages.append(HumanMessage(content=question))
		return messages


class MapAssistant:
	"""Map assistant that processes natural language route requests using LLM and 2GIS API.
	
	This assistant can understand requests like:
	- "Хочу построить маршрут от Красной площади до Тверской"
	- "По дороге зайти в кафе Starbucks"
	- "Найти ближайшую аптеку по пути"
	
	Parameters
	----------
	api_key: Optional[str]
		GROQ API key. If omitted, GROQ_API_KEY env var is used.
	dgis_api_key: Optional[str]
		2GIS API key. If omitted, DGIS_API_KEY env var is used.
	model: str
		Groq model name.
	temperature: float
		Sampling temperature for LLM.
	region_id: str
		2GIS region ID (default: "moscow" for Moscow).
	"""
	
	def __init__(
		self,
		api_key: Optional[str] = None,
		dgis_api_key: Optional[str] = None,
		model: str = DEFAULT_MODEL,
		temperature: float = 0.3,  # Lower temperature for more consistent parsing
		region_id: str = "moscow",
	) -> None:
		self.region_id = region_id
		self._history: List[BaseMessage] = []
		
		# Initialize LLM
		groq_key = api_key or os.getenv("GROQ_API_KEY")
		if not groq_key:
			raise ValueError("GROQ_API_KEY is not set. Provide api_key param or export environment variable.")
		
		# Create ChatGroq with minimal parameters to avoid validation errors
		try:
			self._llm = ChatGroq(
				api_key=groq_key,
				model=model,
				temperature=temperature
			)
		except Exception as e:
			# Fallback: try with even more minimal parameters
			print(f"Warning: ChatGroq initialization failed with full params: {e}")
			try:
				self._llm = ChatGroq(api_key=groq_key)
			except Exception as e2:
				raise ValueError(f"Failed to initialize ChatGroq: {e2}")
		
		# Initialize 2GIS API key
		self.dgis_key = dgis_api_key or os.getenv("DGIS_API_KEY")
		if not self.dgis_key:
			raise ValueError("DGIS_API_KEY is not set. Provide dgis_api_key param or export environment variable.")
		
		# 2GIS API endpoints
		self.places_url = "https://catalog.api.2gis.com/3.0/items"
		self.geocoder_url = "https://catalog.api.2gis.com/3.0/items/geocode"
		self.regions_url = "https://catalog.api.2gis.com/2.0/region/search"
		self.routing_url = "https://routing.api.2gis.com/routing/7.0"
		self.public_transport_url = "https://routing.api.2gis.com/public_transport/2.0"
		
		# Region settings
		self.region_name = os.getenv("DGIS_REGION_NAME", "Москва")  # Default to Moscow
		self.region_id = None  # Will be fetched from Regions API
		
		# System prompt for map assistant
		self._system_prompt = self._build_map_system_prompt()
	
	def _build_map_system_prompt(self) -> str:
		"""Build system prompt for map assistant."""
		return """Ты - умный ассистент по планированию маршрутов. Твоя задача - анализировать запросы пользователей и извлекать информацию о маршрутах.

ВАЖНО: Всегда старайся определить точку отправления, даже если она не указана явно. Используй контекст и здравый смысл.

Ты должен понимать запросы на естественном языке и извлекать:
1. Точку отправления (откуда) - ОБЯЗАТЕЛЬНО попытайся определить
2. Точку назначения (куда) 
3. Промежуточные точки (waypoints) - места, куда пользователь хочет зайти по дороге
4. Тип мест (кафе, аптека, магазин и т.д.)
5. Предпочтения транспорта (такси, общественный транспорт, пешком, максимально быстро и т.д.)

Примеры запросов и извлечения:
- "Хочу построить маршрут от Красной площади до Тверской улицы" 
  → start_point: "Красная площадь", end_point: "Тверская улица", transport_preference: "any"
- "По дороге зайти в кафе Starbucks"
  → waypoint: {"name": "Starbucks", "type": "кафе"}
- "Доехать до офиса 2ГИС на Даниловской набережной"
  → end_point: "офис 2ГИС на Даниловской набережной" (start_point может быть "текущее местоположение")
- "Выйду на станции метро Бульвар Дмитрия Донского"
  → waypoint: {"name": "Бульвар Дмитрия Донского", "type": "станция метро"}
- "По дороге хочу где-нибудь поесть в фастфуде у станции метро"
  → waypoint: {"name": "фастфуд", "type": "фастфуд", "description": "рядом с метро"}
- "Встретиться с другом, хотим где-нибудь поесть в фастфуде у станции метро Бульвар Дмитрия Донского"
  → waypoint: {"name": "фастфуд", "type": "фастфуд", "description": "у станции метро Бульвар Дмитрия Донского"}
- "Хочу только такси до аэропорта"
  → transport_preference: "taxi_only", end_point: "аэропорт"
- "Добраться максимально быстро до центра"
  → transport_preference: "fastest", end_point: "центр"
- "Только наземный транспорт, без метро"
  → transport_preference: "ground_transport_only"
- "Пешком через парк"
  → transport_preference: "walking", route_preference: "через парк"

Твоя задача - вернуть JSON с извлеченной информацией:
{
  "start_point": "описание точки отправления (попытайся определить даже если не указано)",
  "end_point": "описание точки назначения", 
  "waypoints": [
    {
      "name": "название места (без лишних слов)",
      "type": "тип места (кафе, станция метро, ресторан и т.д.)",
      "description": "дополнительное описание"
    }
  ],
  "transport_preference": "предпочтение транспорта (any, taxi_only, public_transport, walking, fastest, ground_transport_only, metro_only, bus_only, tram_only, trolleybus_only, suburban_train_only)",
  "route_preference": "предпочтение маршрута (быстро, короткий, через парк, избегать платных дорог, избегать пробок, через центр, статистика пробок, время отправления: в 15:30, через час, завтра и т.д.)"
}

ПРАВИЛА:
- Если точка отправления не указана, попробуй определить из контекста или используй "текущее местоположение"
- Для станций метро используй только название станции без "станция метро"
- Для типов мест используй простые термины: "кафе", "ресторан", "станция метро", "аптека"
- Для transport_preference используй: "any", "taxi_only", "public_transport", "walking", "fastest", "ground_transport_only", "metro_only", "bus_only", "tram_only", "trolleybus_only", "suburban_train_only"
- Для route_preference извлекай: "быстро" (fastest), "короткий" (shortest), "через парк", "избегать платных дорог", "избегать пробок", "статистика пробок", "через центр", время отправления ("в 15:30", "через час", "завтра")
- Будь точным в извлечении информации"""
	
	async def _geocode_address(self, address: str) -> Optional[Tuple[float, float, str]]:
		"""Geocode an address using 2GIS Geocoder API.
		
		Returns:
			Tuple of (latitude, longitude, formatted_address) or None if not found.
		"""
		logger.info(f"🗺️ 2GIS GEOCODER REQUEST: Geocoding address: '{address}'")
		
		# Get region_id first
		region_id = await self._get_region_id()
		
		params = {
			"q": address,
			"region_id": region_id,
			"key": self.dgis_key,
			"fields": "items.point,items.address_name"
		}
		
		logger.info(f"📤 2GIS GEOCODER REQUEST: URL: {self.geocoder_url}")
		logger.info(f"📤 2GIS GEOCODER REQUEST: Params: {params}")
		
		try:
			# Build full URL for logging
			full_url = f"{self.geocoder_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
			logger.info(f"📤 2GIS GEOCODER REQUEST: Full URL: {full_url}")
			
			async with aiohttp.ClientSession() as session:
				async with session.get(self.geocoder_url, params=params) as response:
					logger.info(f"📥 2GIS GEOCODER RESPONSE: Status {response.status}")
					logger.info(f"📥 2GIS GEOCODER RESPONSE: Headers: {dict(response.headers)}")
					
					if response.status == 200:
						data = await response.json()
						logger.info(f"📥 2GIS GEOCODER RESPONSE: Full data: {json.dumps(data, ensure_ascii=False, indent=2)}")
						
						if data.get("result") and data["result"].get("items"):
							item = data["result"]["items"][0]
							point = item.get("point", {})
							address_name = item.get("address_name", address)
							lat = float(point.get("lat", 0))
							lon = float(point.get("lon", 0))
							
							logger.info(f"✅ 2GIS GEOCODER SUCCESS: Found coordinates {lat}, {lon} for '{address_name}'")
							return (lat, lon, address_name)
						else:
							logger.warning(f"⚠️ 2GIS GEOCODER WARNING: No items found for '{address}'")
					else:
						error_text = await response.text()
						logger.error(f"❌ 2GIS GEOCODER ERROR: HTTP {response.status}")
						logger.error(f"❌ 2GIS GEOCODER ERROR: Response body: {error_text}")
		except Exception as e:
			logger.error(f"❌ 2GIS GEOCODER ERROR: Request failed for '{address}': {e}")
		
		return None
	
	def _improve_search_query(self, name: str, place_type: str) -> str:
		"""Improve search query by cleaning and optimizing it for 2GIS API."""
		# Remove duplicate words and clean the query
		query_parts = []
		
		# Add the main name
		if name:
			# Clean common prefixes/suffixes
			clean_name = name.replace("станция метро ", "").replace("метро ", "").strip()
			query_parts.append(clean_name)
		
		# Add place type only if it's different from name
		if place_type and place_type.lower() not in name.lower():
			# Map common types to better search terms
			type_mapping = {
				"станция метро": "метро",
				"фастфуд": "ресторан быстрого питания",
				"кафе": "кафе",
				"ресторан": "ресторан",
				"аптека": "аптека",
				"магазин": "магазин",
				"банк": "банк"
			}
			improved_type = type_mapping.get(place_type.lower(), place_type)
			if improved_type not in query_parts:
				query_parts.append(improved_type)
		
		# Join parts and limit length
		result = " ".join(query_parts)
		return result[:100]  # Limit query length
	
	def _create_contextual_search_query(self, name: str, place_type: str, context: str = None) -> str:
		"""Create a contextual search query using 2GIS API capabilities."""
		query_parts = []
		
		# Add the main place name/type
		if place_type:
			# Map types to better search terms
			type_mapping = {
				"станция метро": "метро",
				"фастфуд": "ресторан быстрого питания",
				"кафе": "кафе",
				"ресторан": "ресторан",
				"аптека": "аптека",
				"магазин": "магазин",
				"банк": "банк"
			}
			search_type = type_mapping.get(place_type.lower(), place_type)
			query_parts.append(search_type)
		
		# Add specific name if provided
		if name and name.lower() not in ["фастфуд", "кафе", "ресторан", "аптека", "магазин"]:
			clean_name = name.replace("станция метро ", "").replace("метро ", "").strip()
			query_parts.append(clean_name)
		
		# Add contextual information
		if context:
			query_parts.append(context)
		
		# Create enhanced query with geocriteria
		if "метро" in place_type.lower() or "станция" in place_type.lower():
			# For metro stations, add "у станции метро" context
			if len(query_parts) > 1:
				query_parts.append("у станции метро")
		
		result = " ".join(query_parts)
		return result[:150]  # Allow longer queries for better results
	
	async def _get_region_id(self) -> Optional[str]:
		"""Get region_id from 2GIS Regions API."""
		if self.region_id:
			return self.region_id
		
		logger.info(f"🌍 REGIONS API REQUEST: Searching for region: '{self.region_name}'")
		
		params = {
			"q": self.region_name,
			"key": self.dgis_key,
			"fields": "items.id,items.name"
		}
		
		logger.info(f"📤 REGIONS API REQUEST: URL: {self.regions_url}")
		logger.info(f"📤 REGIONS API REQUEST: Params: {params}")
		
		try:
			# Build full URL for logging
			full_url = f"{self.regions_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
			logger.info(f"📤 REGIONS API REQUEST: Full URL: {full_url}")
			
			async with aiohttp.ClientSession() as session:
				async with session.get(self.regions_url, params=params) as response:
					logger.info(f"📥 REGIONS API RESPONSE: Status {response.status}")
					logger.info(f"📥 REGIONS API RESPONSE: Headers: {dict(response.headers)}")
					
					if response.status == 200:
						data = await response.json()
						logger.info(f"📥 REGIONS API RESPONSE: Full data: {json.dumps(data, ensure_ascii=False, indent=2)}")
						
						if data.get("result") and data["result"].get("items"):
							# Find the best match for our region name
							items = data["result"]["items"]
							for item in items:
								item_name = item.get("name", "").lower()
								if self.region_name.lower() in item_name or item_name in self.region_name.lower():
									region_id = str(item.get("id"))
									self.region_id = region_id
									logger.info(f"✅ REGIONS API SUCCESS: Found region_id {region_id} for '{item.get('name')}'")
									return region_id
							
							# If no exact match, use the first result
							if items:
								first_item = items[0]
								region_id = str(first_item.get("id"))
								self.region_id = region_id
								logger.info(f"✅ REGIONS API SUCCESS: Using first result region_id {region_id} for '{first_item.get('name')}'")
								return region_id
						else:
							logger.warning(f"⚠️ REGIONS API WARNING: No items found for '{self.region_name}'")
					else:
						error_text = await response.text()
						logger.error(f"❌ REGIONS API ERROR: HTTP {response.status}")
						logger.error(f"❌ REGIONS API ERROR: Response body: {error_text}")
		except Exception as e:
			logger.error(f"❌ REGIONS API ERROR: Request failed for '{self.region_name}': {e}")
		
		# Fallback to default Moscow region_id
		self.region_id = "32"
		logger.warning(f"⚠️ REGIONS API FALLBACK: Using default region_id 32 (Moscow)")
		return self.region_id
	
	def _create_enhanced_search_query(self, name: str, place_type: str, description: str = None) -> str:
		"""Create an enhanced search query using all available context."""
		query_parts = []
		
		# Add place type
		if place_type:
			type_mapping = {
				"станция метро": "метро",
				"фастфуд": "ресторан быстрого питания",
				"кафе": "кафе",
				"ресторан": "ресторан",
				"аптека": "аптека",
				"магазин": "магазин",
				"банк": "банк"
			}
			search_type = type_mapping.get(place_type.lower(), place_type)
			query_parts.append(search_type)
		
		# Add specific name if it's not generic
		if name and name.lower() not in ["фастфуд", "кафе", "ресторан", "аптека", "магазин", "станция метро"]:
			clean_name = name.replace("станция метро ", "").replace("метро ", "").strip()
			query_parts.append(clean_name)
		
		# Add description as context
		if description:
			# Extract key words from description
			desc_words = description.split()
			# Add relevant words (skip common words)
			skip_words = {"встреча", "с", "другом", "хотим", "где", "нибудь", "поесть", "в", "у", "станции", "метро"}
			for word in desc_words:
				if word.lower() not in skip_words and len(word) > 2:
					query_parts.append(word)
					break  # Add only first relevant word
		
		# Add geocriteria for better results
		if "метро" in place_type.lower() or "станция" in place_type.lower():
			query_parts.append("у станции метро")
		elif "фастфуд" in place_type.lower() or "ресторан" in place_type.lower():
			query_parts.append("рядом с метро")
		
		result = " ".join(query_parts)
		return result[:200]  # Allow even longer queries for enhanced search
	
	def _create_fallback_query(self, name: str, place_type: str) -> str:
		"""Create a simplified fallback query for better search results."""
		# Extract key words from the name
		words = name.split()
		
		# For metro stations, try just the station name
		if "метро" in place_type.lower() or "станция" in place_type.lower():
			# Remove common metro prefixes
			clean_words = [w for w in words if w.lower() not in ["станция", "метро", "ст"]]
			if clean_words:
				return " ".join(clean_words[:2])  # Take first 2 words
		
		# For other places, try just the main words
		if len(words) > 2:
			return " ".join(words[:2])  # Take first 2 words
		
		return name
	
	async def _search_places(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
		"""Search for places using 2GIS Places API.
		
		Returns:
			List of place dictionaries with coordinates and metadata.
		"""
		logger.info(f"🏪 2GIS PLACES REQUEST: Searching for: '{query}' (category: {category})")
		
		# Get region_id first
		region_id = await self._get_region_id()
		
		params = {
			"q": query,
			"region_id": region_id,
			"key": self.dgis_key,
			"fields": "items.point,items.name,items.address_name,items.rubrics"
		}
		
		if category:
			params["rubric_id"] = category
		
		logger.info(f"📤 2GIS PLACES REQUEST: URL: {self.places_url}")
		logger.info(f"📤 2GIS PLACES REQUEST: Params: {params}")
		
		try:
			# Build full URL for logging
			full_url = f"{self.places_url}?" + "&".join([f"{k}={v}" for k, v in params.items()])
			logger.info(f"📤 2GIS PLACES REQUEST: Full URL: {full_url}")
			
			async with aiohttp.ClientSession() as session:
				async with session.get(self.places_url, params=params) as response:
					logger.info(f"📥 2GIS PLACES RESPONSE: Status {response.status}")
					logger.info(f"📥 2GIS PLACES RESPONSE: Headers: {dict(response.headers)}")
					
					if response.status == 200:
						data = await response.json()
						logger.info(f"📥 2GIS PLACES RESPONSE: Full data: {json.dumps(data, ensure_ascii=False, indent=2)}")
						
						if data.get("result") and data["result"].get("items"):
							items = data["result"]["items"]
							logger.info(f"✅ 2GIS PLACES SUCCESS: Found {len(items)} places for '{query}'")
							for i, item in enumerate(items[:3]):  # Log first 3 items
								name = item.get("name", "Unknown")
								address = item.get("address_name", "Unknown")
								logger.debug(f"✅ 2GIS PLACES SUCCESS: Item {i+1}: {name} at {address}")
							return items
						else:
							logger.warning(f"⚠️ 2GIS PLACES WARNING: No items found for '{query}'")
					else:
						error_text = await response.text()
						logger.error(f"❌ 2GIS PLACES ERROR: HTTP {response.status}")
						logger.error(f"❌ 2GIS PLACES ERROR: Response body: {error_text}")
		except Exception as e:
			logger.error(f"❌ 2GIS PLACES ERROR: Request failed for '{query}': {e}")
		
		return []
	
	async def _get_routing_options(self, start_point: RoutePoint, end_point: RoutePoint, 
								   waypoints: List[RoutePoint] = None, 
								   transport_preference: str = "any",
								   route_preference: str = None) -> List[Route]:
		"""Get routing options using 2GIS Routing API and Public Transport API."""
		logger.info(f"🚗 ROUTING REQUEST: Getting routes from {start_point.name} to {end_point.name}")
		logger.info(f"🚗 ROUTING REQUEST: Transport preference: {transport_preference}")
		logger.info(f"🚗 ROUTING REQUEST: Route preference: {route_preference}")
		
		routes = []
		
		# Determine which APIs to use based on transport preference
		if transport_preference == "walking":
			routes.extend(await self._get_walking_routes(start_point, end_point, waypoints, route_preference))
		elif transport_preference == "taxi_only":
			routes.extend(await self._get_taxi_routes(start_point, end_point, waypoints, route_preference))
		elif transport_preference in ["public_transport", "metro_only", "bus_only", "tram_only", "trolleybus_only", "suburban_train_only"]:
			start_time = self._parse_time_preference(route_preference)
			routes.extend(await self._get_public_transport_routes(start_point, end_point, waypoints, transport_preference, start_time))
		elif transport_preference == "ground_transport_only":
			start_time = self._parse_time_preference(route_preference)
			routes.extend(await self._get_ground_transport_routes(start_point, end_point, waypoints, transport_preference, start_time))
		elif transport_preference == "fastest":
			# Get all options and choose fastest
			all_routes = []
			start_time = self._parse_time_preference(route_preference)
			all_routes.extend(await self._get_taxi_routes(start_point, end_point, waypoints, route_preference))
			all_routes.extend(await self._get_public_transport_routes(start_point, end_point, waypoints, "public_transport", start_time))
			# Sort by duration and take fastest
			all_routes.sort(key=lambda r: r.total_duration)
			routes = all_routes[:3]  # Top 3 fastest
		else:  # "any"
			# Get multiple options
			start_time = self._parse_time_preference(route_preference)
			routes.extend(await self._get_taxi_routes(start_point, end_point, waypoints, route_preference))
			routes.extend(await self._get_public_transport_routes(start_point, end_point, waypoints, "public_transport", start_time))
		
		logger.info(f"✅ ROUTING SUCCESS: Found {len(routes)} route options")
		return routes
	
	async def _get_taxi_routes(self, start_point: RoutePoint, end_point: RoutePoint, 
							   waypoints: List[RoutePoint] = None, 
							   route_preference: str = None) -> List[Route]:
		"""Get taxi routes using 2GIS Routing API."""
		logger.info(f"🚕 TAXI ROUTING: Getting taxi routes")
		
		# Build request payload
		payload = {
			"locale": "ru",
			"source": {
				"name": start_point.name,
				"point": {
					"lat": start_point.latitude,
					"lon": start_point.longitude
				}
			},
			"target": {
				"name": end_point.name,
				"point": {
					"lat": end_point.latitude,
					"lon": end_point.longitude
				}
			},
			"transport": ["taxi"]
		}
		
		# Add routing parameters based on preferences
		params = self._build_routing_params(route_preference)
		if params:
			payload["params"] = params
		
		# Add waypoints if provided
		if waypoints:
			payload["intermediate_points"] = [
				{
					"name": wp.name,
					"point": {
						"lat": wp.latitude,
						"lon": wp.longitude
					}
				}
				for wp in waypoints
			]
		
		return await self._make_routing_request(payload, "taxi")
	
	async def _get_public_transport_routes(self, start_point: RoutePoint, end_point: RoutePoint, 
										   waypoints: List[RoutePoint] = None,
										   transport_preference: str = None,
										   start_time: int = None) -> List[Route]:
		"""Get public transport routes using 2GIS Public Transport API."""
		logger.info(f"🚌 PUBLIC TRANSPORT ROUTING: Getting public transport routes")
		logger.info(f"🚌 PUBLIC TRANSPORT ROUTING: Transport preference: {transport_preference}")
		logger.info(f"🚌 PUBLIC TRANSPORT ROUTING: Start time: {start_time}")
		
		# Determine transport types based on preference
		transport_types = self._get_transport_types(transport_preference)
		
		# Build request payload
		payload = {
			"locale": "ru",
			"source": {
				"name": start_point.name,
				"point": {
					"lat": start_point.latitude,
					"lon": start_point.longitude
				}
			},
			"target": {
				"name": end_point.name,
				"point": {
					"lat": end_point.latitude,
					"lon": end_point.longitude
				}
			},
			"transport": transport_types
		}
		
		# Add start time if provided
		if start_time:
			payload["start_time"] = start_time
		
		# Add waypoints if provided
		if waypoints:
			payload["intermediate_points"] = [
				{
					"name": wp.name,
					"point": {
						"lat": wp.latitude,
						"lon": wp.longitude
					}
				}
				for wp in waypoints
			]
		
		return await self._make_public_transport_request(payload)
	
	async def _get_ground_transport_routes(self, start_point: RoutePoint, end_point: RoutePoint, 
										   waypoints: List[RoutePoint] = None,
										   transport_preference: str = None,
										   start_time: int = None) -> List[Route]:
		"""Get ground transport routes (excluding metro)."""
		logger.info(f"🚌 GROUND TRANSPORT ROUTING: Getting ground transport routes")
		logger.info(f"🚌 GROUND TRANSPORT ROUTING: Transport preference: {transport_preference}")
		logger.info(f"🚌 GROUND TRANSPORT ROUTING: Start time: {start_time}")
		
		payload = {
			"locale": "ru",
			"source": {
				"name": start_point.name,
				"point": {
					"lat": start_point.latitude,
					"lon": start_point.longitude
				}
			},
			"target": {
				"name": end_point.name,
				"point": {
					"lat": end_point.latitude,
					"lon": end_point.longitude
				}
			},
			"transport": ["bus", "tram", "shuttle_bus"]  # Exclude metro
		}
		
		# Add start time if provided
		if start_time:
			payload["start_time"] = start_time
		
		if waypoints:
			payload["intermediate_points"] = [
				{
					"name": wp.name,
					"point": {
						"lat": wp.latitude,
						"lon": wp.longitude
					}
				}
				for wp in waypoints
			]
		
		return await self._make_public_transport_request(payload)
	
	async def _get_walking_routes(self, start_point: RoutePoint, end_point: RoutePoint, 
								  waypoints: List[RoutePoint] = None,
								  route_preference: str = None) -> List[Route]:
		"""Get walking routes using 2GIS Routing API."""
		logger.info(f"🚶 WALKING ROUTING: Getting walking routes")
		
		payload = {
			"locale": "ru",
			"source": {
				"name": start_point.name,
				"point": {
					"lat": start_point.latitude,
					"lon": start_point.longitude
				}
			},
			"target": {
				"name": end_point.name,
				"point": {
					"lat": end_point.latitude,
					"lon": end_point.longitude
				}
			},
			"transport": ["walking"]
		}
		
		# Add pedestrian-specific parameters
		params = self._build_pedestrian_params(route_preference)
		if params:
			payload["params"] = params
		
		if waypoints:
			payload["intermediate_points"] = [
				{
					"name": wp.name,
					"point": {
						"lat": wp.latitude,
						"lon": wp.longitude
					}
				}
				for wp in waypoints
			]
		
		return await self._make_routing_request(payload, "walking")
	
	async def _make_routing_request(self, payload: Dict[str, Any], transport_type: str) -> List[Route]:
		"""Make request to 2GIS Routing API."""
		params = {"key": self.dgis_key}
		
		logger.info(f"📤 ROUTING API REQUEST: URL: {self.routing_url}")
		logger.info(f"📤 ROUTING API REQUEST: Params: {params}")
		logger.info(f"📤 ROUTING API REQUEST: Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(self.routing_url, params=params, json=payload) as response:
					logger.info(f"📥 ROUTING API RESPONSE: Status {response.status}")
					logger.info(f"📥 ROUTING API RESPONSE: Headers: {dict(response.headers)}")
					
					if response.status == 200:
						data = await response.json()
						logger.info(f"📥 ROUTING API RESPONSE: Full data: {json.dumps(data, ensure_ascii=False, indent=2)}")
						
						return self._parse_routing_response(data, transport_type)
					else:
						error_text = await response.text()
						logger.error(f"❌ ROUTING API ERROR: HTTP {response.status}")
						logger.error(f"❌ ROUTING API ERROR: Response body: {error_text}")
		except Exception as e:
			logger.error(f"❌ ROUTING API ERROR: Request failed: {e}")
		
		return []
	
	async def _make_public_transport_request(self, payload: Dict[str, Any]) -> List[Route]:
		"""Make request to 2GIS Public Transport API."""
		params = {"key": self.dgis_key}
		
		logger.info(f"📤 PUBLIC TRANSPORT API REQUEST: URL: {self.public_transport_url}")
		logger.info(f"📤 PUBLIC TRANSPORT API REQUEST: Params: {params}")
		logger.info(f"📤 PUBLIC TRANSPORT API REQUEST: Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(self.public_transport_url, params=params, json=payload) as response:
					logger.info(f"📥 PUBLIC TRANSPORT API RESPONSE: Status {response.status}")
					logger.info(f"📥 PUBLIC TRANSPORT API RESPONSE: Headers: {dict(response.headers)}")
					
					if response.status == 200:
						data = await response.json()
						logger.info(f"📥 PUBLIC TRANSPORT API RESPONSE: Full data: {json.dumps(data, ensure_ascii=False, indent=2)}")
						
						return self._parse_public_transport_response(data)
					else:
						error_text = await response.text()
						logger.error(f"❌ PUBLIC TRANSPORT API ERROR: HTTP {response.status}")
						logger.error(f"❌ PUBLIC TRANSPORT API ERROR: Response body: {error_text}")
		except Exception as e:
			logger.error(f"❌ PUBLIC TRANSPORT API ERROR: Request failed: {e}")
		
		return []
	
	def _parse_routing_response(self, data: Dict[str, Any], transport_type: str) -> List[Route]:
		"""Parse routing API response."""
		routes = []
		
		if isinstance(data, list):
			for i, route_data in enumerate(data):
				route = self._parse_single_route(route_data, f"{transport_type}_{i+1}")
				if route:
					routes.append(route)
		
		return routes
	
	def _parse_public_transport_response(self, data: List[Dict[str, Any]]) -> List[Route]:
		"""Parse public transport API response - simplified version."""
		routes = []
		
		for i, route_data in enumerate(data):
			# Create a simplified route with raw data
			route_id = f"public_transport_{i+1}"
			total_distance = route_data.get("total_distance", 0)
			total_duration = route_data.get("total_duration", 0)
			transfer_count = route_data.get("transfer_count", 0)
			
			# Extract transport types from segments
			transport_types = set()
			segments_data = route_data.get("segments", [])
			for segment in segments_data:
				if segment.get("type") == "passage":
					routes_info = segment.get("routes", [])
					for route_info in routes_info:
						transport_types.add(route_info.get("subtype", "unknown"))
				elif segment.get("type") == "walkway":
					transport_types.add("walking")
				elif segment.get("type") == "crossing":
					transport_types.add("metro")
			
			# Create summary
			summary = f"Маршрут {route_id}: {total_duration//60} мин, {total_distance//1000} км"
			if transfer_count > 0:
				summary += f", {transfer_count} пересадок"
			
			# Create simplified segments
			segments = []
			for j, segment_data in enumerate(segments_data):
				segment = RouteSegment(
					segment_type=segment_data.get("type", "unknown"),
					distance=segment_data.get("distance", 0),
					duration=segment_data.get("moving_duration", 0),
					transport_type=segment_data.get("routes", [{}])[0].get("subtype") if segment_data.get("routes") else None,
					route_name=", ".join(segment_data.get("routes", [{}])[0].get("names", [])) if segment_data.get("routes") else None,
					description=segment_data.get("waypoint", {}).get("name", "")
				)
				segments.append(segment)
			
			route = Route(
				route_id=route_id,
				total_distance=total_distance,
				total_duration=total_duration,
				transfer_count=transfer_count,
				transport_types=list(transport_types),
				segments=segments,
				summary=summary,
				raw_data=route_data  # Include raw data
			)
			routes.append(route)
		
		return routes
	
	def _parse_single_route(self, route_data: Dict[str, Any], route_id: str) -> Optional[Route]:
		"""Parse a single route from API response."""
		try:
			segments = []
			
			# Extract route segments from segments field (for public transport) or waypoints (for routing)
			segments_data = route_data.get("segments", [])
			if not segments_data:
				# Fallback to waypoints for routing API
				segments_data = route_data.get("waypoints", [])
			
			for segment_data in segments_data:
				segment = self._parse_route_segment(segment_data)
				if segment:
					segments.append(segment)
			
			# Create route summary
			total_distance = route_data.get("total_distance", 0)
			total_duration = route_data.get("total_duration", 0)
			transfer_count = route_data.get("transfer_count", 0)
			transport_types = route_data.get("transport", [])
			
			summary = f"Маршрут {route_id}: {total_duration//60} мин, {total_distance//1000} км"
			if transfer_count > 0:
				summary += f", {transfer_count} пересадок"
			
			return Route(
				route_id=route_id,
				total_distance=total_distance,
				total_duration=total_duration,
				transfer_count=transfer_count,
				transport_types=transport_types,
				segments=segments,
				summary=summary
			)
		except Exception as e:
			logger.error(f"❌ ROUTE PARSING ERROR: Failed to parse route {route_id}: {e}")
			return None
	
	def _parse_route_segment(self, segment_data: Dict[str, Any]) -> Optional[RouteSegment]:
		"""Parse a single route segment."""
		try:
			segment_type = segment_data.get("type", "unknown")
			distance = segment_data.get("distance", 0)
			duration = segment_data.get("moving_duration", 0)
			
			# Extract transport information
			transport_type = None
			route_name = None
			description = None
			
			# Handle different segment types from 2GIS Public Transport API
			if segment_type == "passage":
				# Public transport segment (bus, metro, etc.)
				routes = segment_data.get("routes", [])
				if routes:
					route_info = routes[0]
					transport_type = route_info.get("subtype")
					route_names = route_info.get("names", [])
					if route_names:
						route_name = ", ".join(route_names)
				
				# Get description from waypoint
				waypoint = segment_data.get("waypoint", {})
				description = waypoint.get("name", "")
				
				# Add waiting time to description
				waiting_duration = segment_data.get("waiting_duration", 0)
				if waiting_duration > 0:
					description += f" (ожидание {waiting_duration//60} мин)"
					
			elif segment_type == "walkway":
				# Walking segment
				transport_type = "walking"
				waypoint = segment_data.get("waypoint", {})
				description = waypoint.get("comment", waypoint.get("name", ""))
				
			elif segment_type == "crossing":
				# Metro station crossing
				transport_type = "metro"
				waypoint = segment_data.get("waypoint", {})
				description = waypoint.get("comment", waypoint.get("name", ""))
				
			else:
				# Unknown segment type
				waypoint = segment_data.get("waypoint", {})
				description = waypoint.get("comment", waypoint.get("name", ""))
			
			return RouteSegment(
				segment_type=segment_type,
				distance=distance,
				duration=duration,
				transport_type=transport_type,
				route_name=route_name,
				description=description
			)
		except Exception as e:
			logger.error(f"❌ SEGMENT PARSING ERROR: Failed to parse segment: {e}")
			return None
	
	def _build_routing_params(self, route_preference: str = None) -> Optional[Dict[str, Any]]:
		"""Build routing parameters based on user preferences."""
		params = {}
		
		# Route mode (fastest/shortest)
		if route_preference:
			if "быстро" in route_preference.lower() or "скоро" in route_preference.lower():
				params["route_mode"] = "fastest"
			elif "короткий" in route_preference.lower() or "близко" in route_preference.lower():
				params["route_mode"] = "shortest"
		
		# Traffic mode (jam/statistics)
		if route_preference:
			if "пробки" in route_preference.lower() or "заторы" in route_preference.lower():
				params["traffic_mode"] = "jam"
			elif "статистика" in route_preference.lower():
				params["traffic_mode"] = "statistics"
		
		# Filters for avoiding certain road types
		filters = []
		if route_preference:
			if "платные" in route_preference.lower():
				filters.append("toll_road")
			if "грунтовые" in route_preference.lower():
				filters.append("dirt_road")
			if "парк" in route_preference.lower() or "зеленые" in route_preference.lower():
				# For park routes, avoid highways
				filters.append("highway")
		
		if filters:
			params["filters"] = filters
		
		# Need altitudes for elevation info
		if route_preference and ("высота" in route_preference.lower() or "горы" in route_preference.lower()):
			params["need_altitudes"] = True
		
		return params if params else None
	
	def _build_pedestrian_params(self, route_preference: str = None) -> Optional[Dict[str, Any]]:
		"""Build pedestrian-specific routing parameters."""
		params = {}
		
		# Pedestrian-specific settings
		pedestrian_params = {}
		
		# Use indoor routing
		if route_preference and ("здание" in route_preference.lower() or "внутри" in route_preference.lower()):
			pedestrian_params["use_indoor"] = True
		
		# Use navigation instructions
		if route_preference and ("инструкции" in route_preference.lower() or "навигация" in route_preference.lower()):
			pedestrian_params["use_instructions"] = True
		
		if pedestrian_params:
			params["pedestrian"] = pedestrian_params
		
		# Add general routing parameters
		general_params = self._build_routing_params(route_preference)
		if general_params:
			params.update(general_params)
		
		return params if params else None
	
	def _get_transport_types(self, transport_preference: str = None) -> List[str]:
		"""Get transport types based on user preference."""
		# Default transport types
		default_transports = [
			"metro", "bus", "tram", "trolleybus", "shuttle_bus",
			"suburban_train", "aeroexpress", "light_metro", "monorail",
			"funicular_railway", "river_transport", "cable_car",
			"light_rail", "premetro", "mcc", "mcd"
		]
		
		if not transport_preference:
			return ["metro", "bus", "tram", "trolleybus", "shuttle_bus"]
		
		transport_preference = transport_preference.lower()
		
		# Specific transport type preferences
		if "метро" in transport_preference or "metro" in transport_preference:
			return ["metro", "light_metro", "premetro"]
		elif "автобус" in transport_preference or "bus" in transport_preference:
			return ["bus", "shuttle_bus"]
		elif "трамвай" in transport_preference or "tram" in transport_preference:
			return ["tram"]
		elif "троллейбус" in transport_preference or "trolleybus" in transport_preference:
			return ["trolleybus"]
		elif "электричка" in transport_preference or "suburban" in transport_preference:
			return ["suburban_train", "aeroexpress"]
		elif "наземный" in transport_preference or "ground" in transport_preference:
			return ["bus", "tram", "trolleybus", "shuttle_bus"]
		elif "только метро" in transport_preference:
			return ["metro"]
		elif "без метро" in transport_preference or "наземный транспорт" in transport_preference:
			return ["bus", "tram", "trolleybus", "shuttle_bus"]
		else:
			return default_transports
	
	def _parse_time_preference(self, route_preference: str = None) -> Optional[int]:
		"""Parse time preference from route_preference string."""
		if not route_preference:
			return None
		
		import re
		from datetime import datetime, timedelta
		
		route_preference = route_preference.lower()
		
		# Parse specific times
		time_patterns = [
			r'(\d{1,2}):(\d{2})',  # HH:MM format
			r'в (\d{1,2}):(\d{2})',  # "в HH:MM"
			r'(\d{1,2}) часов',  # "X часов"
			r'(\d{1,2}) час',  # "X час"
		]
		
		for pattern in time_patterns:
			match = re.search(pattern, route_preference)
			if match:
				if ':' in pattern:
					hour, minute = int(match.group(1)), int(match.group(2))
					# Create datetime for today with specified time
					today = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
					return int(today.timestamp())
				else:
					hour = int(match.group(1))
					today = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
					return int(today.timestamp())
		
		# Parse relative times
		if "через час" in route_preference:
			future_time = datetime.now() + timedelta(hours=1)
			return int(future_time.timestamp())
		elif "через полчаса" in route_preference or "через 30 минут" in route_preference:
			future_time = datetime.now() + timedelta(minutes=30)
			return int(future_time.timestamp())
		elif "завтра" in route_preference:
			tomorrow = datetime.now() + timedelta(days=1)
			return int(tomorrow.timestamp())
		
		return None
	
	def _clean_llm_response(self, content: str) -> str:
		"""Clean LLM response from thinking tags and extra text."""
		import re
		
		# Remove thinking tags like <think>...</think>
		content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
		
		# Remove markdown code blocks
		content = re.sub(r'```json\s*', '', content)
		content = re.sub(r'```\s*', '', content)
		
		# Remove extra whitespace and newlines
		content = content.strip()
		
		# Remove any text before the first { and after the last }
		start = content.find('{')
		end = content.rfind('}')
		if start != -1 and end != -1:
			content = content[start:end + 1]
		
		return content
	
	def _parse_route_request(self, request: str) -> Dict[str, Any]:
		"""Parse user request using LLM to extract route information."""
		logger.info(f"🤖 GROQ REQUEST: Parsing route request: '{request}'")
		
		messages = [
			SystemMessage(content=self._system_prompt),
			HumanMessage(content=f"Проанализируй этот запрос и извлеки информацию о маршруте: {request}")
		]
		
		logger.info(f"📤 GROQ REQUEST: Sending to LLM with {len(messages)} messages")
		logger.info(f"📤 GROQ REQUEST: System prompt: {self._system_prompt}")
		logger.info(f"📤 GROQ REQUEST: User message: {messages[1].content}")
		
		try:
			response = self._llm.invoke(messages)
			content = response.content.strip()
			
			logger.info(f"📥 GROQ RESPONSE: Received response ({len(content)} chars)")
			logger.info(f"📥 GROQ RESPONSE: Full response: {content}")
			
			# Clean the response from LLM thinking tags and extra text
			cleaned_content = self._clean_llm_response(content)
			
			# Try to extract JSON from cleaned response
			start = cleaned_content.find('{')
			end = cleaned_content.rfind('}')
			if start != -1 and end != -1:
				json_str = cleaned_content[start:end + 1]
				parsed = json.loads(json_str)
				logger.info(f"✅ GROQ SUCCESS: Parsed JSON successfully")
				logger.info(f"✅ GROQ SUCCESS: Parsed data: {json.dumps(parsed, ensure_ascii=False, indent=2)}")
				return parsed
			else:
				logger.warning(f"⚠️ GROQ WARNING: No JSON found in response")
		except json.JSONDecodeError as e:
			logger.error(f"❌ GROQ ERROR: JSON decode error: {e}")
		except Exception as e:
			logger.error(f"❌ GROQ ERROR: Request failed: {e}")
		
		return {}
	
	async def process_route_request(self, request: str) -> EnhancedRouteResponse:
		"""Process a natural language route request and return route points with friendly text.
		
		Args:
			request: Natural language request for route planning
			
		Returns:
			RouteResponse with points array and friendly text
		"""
		logger.info(f"🚀 MAP ASSISTANT: Starting route processing for: '{request}'")
		
		try:
			# Parse the request using LLM
			logger.info(f"📝 MAP ASSISTANT: Step 1 - Parsing request with LLM")
			parsed_info = self._parse_route_request(request)
			
			if not parsed_info:
				logger.error(f"❌ MAP ASSISTANT: Failed to parse request")
				return EnhancedRouteResponse(
					points=[],
					text="Извините, не удалось понять ваш запрос. Попробуйте переформулировать.",
					success=False,
					error_message="Failed to parse request"
				)
			
			logger.info(f"📝 MAP ASSISTANT: Step 2 - Processing parsed info: {parsed_info}")
			points = []
			friendly_text_parts = []
			
			# Process start point
			if parsed_info.get("start_point"):
				logger.info(f"📍 MAP ASSISTANT: Step 3a - Processing start point: {parsed_info['start_point']}")
				coords = await self._geocode_address(parsed_info["start_point"])
				if coords:
					lat, lon, address = coords
					points.append(RoutePoint(
						name=parsed_info["start_point"],
						latitude=lat,
						longitude=lon,
						point_type="start",
						address=address
					))
					friendly_text_parts.append(f"📍 Точка отправления: {address}")
					logger.info(f"✅ MAP ASSISTANT: Start point added: {address}")
				else:
					logger.warning(f"⚠️ MAP ASSISTANT: Start point not found: {parsed_info['start_point']}")
			else:
				logger.info(f"📍 MAP ASSISTANT: No start point specified, using current location")
				# Add a placeholder start point
				points.append(RoutePoint(
					name="Текущее местоположение",
					latitude=55.755814,  # Moscow center coordinates
					longitude=37.617635,
					point_type="start",
					address="Текущее местоположение"
				))
				friendly_text_parts.append(f"📍 Точка отправления: Текущее местоположение")
				logger.info(f"✅ MAP ASSISTANT: Start point added: Текущее местоположение")
			
			# Process waypoints
			waypoints = parsed_info.get("waypoints", [])
			logger.info(f"🛍️ MAP ASSISTANT: Step 3b - Processing {len(waypoints)} waypoints")
			for i, waypoint in enumerate(waypoints):
				if isinstance(waypoint, dict):
					name = waypoint.get("name", "")
					place_type = waypoint.get("type", "")
					description = waypoint.get("description", "")
					
					logger.info(f"🛍️ MAP ASSISTANT: Processing waypoint {i+1}: {name} ({place_type}) - {description}")
					
					# Create contextual search query
					context = None
					if description:
						context = description
					
					search_query = self._create_contextual_search_query(name, place_type, context)
					logger.info(f"🔍 MAP ASSISTANT: Contextual search query: '{search_query}'")
					places = await self._search_places(search_query)
					
					if places:
						place = places[0]
						point = place.get("point", {})
						points.append(RoutePoint(
							name=place.get("name", name),
							latitude=float(point.get("lat", 0)),
							longitude=float(point.get("lon", 0)),
							point_type="waypoint",
							description=waypoint.get("description"),
							address=place.get("address_name")
						))
						friendly_text_parts.append(f"🛍️ По дороге: {place.get('name')} ({place.get('address_name', '')})")
						logger.info(f"✅ MAP ASSISTANT: Waypoint {i+1} added: {place.get('name')}")
					else:
						# Try fallback search with simplified query
						logger.info(f"🔄 MAP ASSISTANT: Trying fallback search for waypoint {i+1}")
						fallback_query = self._create_fallback_query(name, place_type)
						logger.info(f"🔄 MAP ASSISTANT: Fallback query: '{fallback_query}'")
						fallback_places = await self._search_places(fallback_query)
						
						if fallback_places:
							place = fallback_places[0]
							point = place.get("point", {})
							points.append(RoutePoint(
								name=place.get("name", name),
								latitude=float(point.get("lat", 0)),
								longitude=float(point.get("lon", 0)),
								point_type="waypoint",
								description=waypoint.get("description"),
								address=place.get("address_name")
							))
							friendly_text_parts.append(f"🛍️ По дороге: {place.get('name')} ({place.get('address_name', '')})")
							logger.info(f"✅ MAP ASSISTANT: Waypoint {i+1} added via fallback: {place.get('name')}")
						else:
							# Try one more time with enhanced contextual search
							logger.info(f"🔄 MAP ASSISTANT: Trying enhanced contextual search for waypoint {i+1}")
							enhanced_query = self._create_enhanced_search_query(name, place_type, description)
							logger.info(f"🔄 MAP ASSISTANT: Enhanced query: '{enhanced_query}'")
							enhanced_places = await self._search_places(enhanced_query)
							
							if enhanced_places:
								place = enhanced_places[0]
								point = place.get("point", {})
								points.append(RoutePoint(
									name=place.get("name", name),
									latitude=float(point.get("lat", 0)),
									longitude=float(point.get("lon", 0)),
									point_type="waypoint",
									description=waypoint.get("description"),
									address=place.get("address_name")
								))
								friendly_text_parts.append(f"🛍️ По дороге: {place.get('name')} ({place.get('address_name', '')})")
								logger.info(f"✅ MAP ASSISTANT: Waypoint {i+1} added via enhanced search: {place.get('name')}")
							else:
								logger.warning(f"⚠️ MAP ASSISTANT: Waypoint {i+1} not found even with enhanced search: {name}")
			
			# Process end point
			if parsed_info.get("end_point"):
				logger.info(f"🎯 MAP ASSISTANT: Step 3c - Processing end point: {parsed_info['end_point']}")
				coords = await self._geocode_address(parsed_info["end_point"])
				if coords:
					lat, lon, address = coords
					points.append(RoutePoint(
						name=parsed_info["end_point"],
						latitude=lat,
						longitude=lon,
						point_type="end",
						address=address
					))
					friendly_text_parts.append(f"🎯 Точка назначения: {address}")
					logger.info(f"✅ MAP ASSISTANT: End point added: {address}")
				else:
					logger.warning(f"⚠️ MAP ASSISTANT: End point not found: {parsed_info['end_point']}")
			
			# Generate friendly response
			logger.info(f"📝 MAP ASSISTANT: Step 4 - Generating response with {len(points)} points")
			if points:
				# Extract transport preference
				transport_preference = parsed_info.get("transport_preference", "any")
				route_preference = parsed_info.get("route_preference")
				logger.info(f"🚗 MAP ASSISTANT: Step 5 - Building routes with transport preference: {transport_preference}")
				logger.info(f"🚗 MAP ASSISTANT: Step 5 - Building routes with route preference: {route_preference}")
				
				# Find start and end points
				start_point = None
				end_point = None
				waypoints = []
				
				for point in points:
					if point.point_type == "start":
						start_point = point
					elif point.point_type == "end":
						end_point = point
					elif point.point_type == "waypoint":
						waypoints.append(point)
				
				# Build routes if we have start and end points
				routes = []
				if start_point and end_point:
					logger.info(f"🚗 MAP ASSISTANT: Building routes from {start_point.name} to {end_point.name}")
					routes = await self._get_routing_options(start_point, end_point, waypoints, transport_preference, route_preference)
					logger.info(f"✅ MAP ASSISTANT: Built {len(routes)} route options")
				
				# Generate friendly text
				friendly_text = f"✅ Маршрут построен!\n\n" + "\n".join(friendly_text_parts)
				
				if routes:
					friendly_text += f"\n\n🚗 Доступные варианты маршрутов:\n"
					for i, route in enumerate(routes[:3], 1):  # Show top 3 routes
						friendly_text += f"{i}. {route.summary}\n"
						if route.transport_types:
							transport_names = {
								"taxi": "🚕 Такси",
								"bus": "🚌 Автобус", 
								"metro": "🚇 Метро",
								"tram": "🚋 Трамвай",
								"shuttle_bus": "🚐 Маршрутка",
								"walking": "🚶 Пешком"
							}
							transport_list = [transport_names.get(t, t) for t in route.transport_types]
							friendly_text += f"   Транспорт: {', '.join(transport_list)}\n"
				else:
					transport_preference_text = {
						"any": "любым транспортом",
						"taxi_only": "только такси",
						"public_transport": "общественным транспортом",
						"walking": "пешком",
						"fastest": "максимально быстро",
						"ground_transport_only": "только наземным транспортом"
					}
					transport_text = transport_preference_text.get(transport_preference, "любым транспортом")
					friendly_text += f"\n\n🚶‍♂️ Рекомендуемый способ передвижения: {transport_text}"
				
				if len(points) > 2:
					friendly_text += f"\n\n💡 Совет: У вас {len(points)-2} промежуточных остановок. Учитывайте время на каждую остановку при планировании."
				
				logger.info(f"✅ MAP ASSISTANT: SUCCESS - Route completed with {len(points)} points and {len(routes)} route options")
				logger.debug(f"✅ MAP ASSISTANT: Final response text: {friendly_text}")
				
				return EnhancedRouteResponse(
					points=points,
					routes=routes,
					text=friendly_text,
					success=True
				)
			else:
				logger.error(f"❌ MAP ASSISTANT: FAILED - No valid points found")
				return EnhancedRouteResponse(
					points=[],
					text="К сожалению, не удалось найти указанные места. Проверьте правильность названий.",
					success=False,
					error_message="No valid points found"
				)
		
		except Exception as e:
			logger.error(f"❌ MAP ASSISTANT: EXCEPTION - {str(e)}")
			return EnhancedRouteResponse(
				points=[],
				text="Произошла ошибка при обработке запроса. Попробуйте еще раз.",
				success=False,
				error_message=str(e)
			)
	
	def get_history(self) -> List[Dict[str, str]]:
		"""Return chat history as list of dicts: {role, content}."""
		out: List[Dict[str, str]] = []
		for msg in self._history:
			role = (
				"user" if isinstance(msg, HumanMessage) else "assistant" if isinstance(msg, AIMessage) else "system"
			)
			out.append({"role": role, "content": msg.content})
		return out
	
	def reset_history(self) -> None:
		"""Clear conversation history."""
		self._history.clear()


__all__ = ["LangChainGroqChatbot", "MapAssistant", "RoutePoint", "RouteResponse", "RouteSegment", "Route", "EnhancedRouteResponse"]
