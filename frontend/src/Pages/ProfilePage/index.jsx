import React, {useState} from 'react';
import {useNavigate} from 'react-router-dom';

const ProfilePage = () => {
  const navigate = useNavigate();

  const [name, setName] = useState('Даша');
  const [surname, setSurname] = useState('Короленко');
  const [email, setEmail] = useState('dariaexplorer@gmail.com');
  const [phone, setPhone] = useState('+7 915 450 03 46');

  const [useWheelchair, setUseWheelchair] = useState(true);
  const [mentalHealthFeatures, setMentalHealthFeatures] = useState(true);
  const [buildSafeRoutes, setBuildSafeRoutes] = useState(true);
  const [useRestroomsOften, setUseRestroomsOften] = useState(true);

  const handleSave = () => {
    console.log('Profile saved!');
    navigate('/');
  };

  return (
    <div className='bg-[#222222] text-white h-screen flex flex-col'>
      {/* Header */}
      <div className='flex  items-center p-4 border-b border-gray-700 justify-between'>
        <button onClick={() => navigate('/')} className='text-white text-xl'>
          X
        </button>
        <button onClick={handleSave} className='text-green-500 text-base'>
          Сохранить
        </button>
      </div>

      <div className='flex-1 overflow-y-auto p-4 space-y-6'>
        {/* Profile Photo Section */}
        <h1 className='text-lg font-semibold text-center'>Редактирование профиля</h1>
        <div className='flex items-center space-x-4'>
          <div className='w-20 h-20 bg-gray-600 rounded-full flex items-center justify-center'>
            {/* Placeholder for image */}
          </div>
          <button className='text-blue-500 text-sm'>ВЫБЕРИТЕ ФОТОГРАФИЮ</button>
        </div>

        {/* Personal Information Fields */}
        <div className='space-y-4'>
          <div>
            <label className='text-gray-400 text-sm'>Ваше имя</label>
            <input
              type='text'
              value={name}
              onChange={(e) => setName(e.target.value)}
              className='w-full bg-transparent border-b border-gray-700 py-2 text-white focus:outline-none'
            />
          </div>
          <div>
            <label className='text-gray-400 text-sm'>Ваша фамилия</label>
            <input
              type='text'
              value={surname}
              onChange={(e) => setSurname(e.target.value)}
              className='w-full bg-transparent border-b border-gray-700 py-2 text-white focus:outline-none'
            />
          </div>
          <div>
            <label className='text-gray-400 text-sm'>Ваш e-mail</label>
            <input
              type='email'
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className='w-full bg-transparent border-b border-gray-700 py-2 text-white focus:outline-none'
            />
          </div>
          <div>
            <label className='text-gray-400 text-sm'>Телефон</label>
            <input
              type='tel'
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className='w-full bg-transparent border-b border-gray-700 py-2 text-white focus:outline-none'
            />
            <button className='text-blue-500 text-sm mt-2'>Изменить номер</button>
          </div>
        </div>

        {/* Adaptive Routes Section */}
        <div className='space-y-4 pt-4 border-t border-gray-700'>
          <h2 className='text-lg font-semibold'>Адаптивные маршруты</h2>
          <div className='space-y-4'>
            {/* Toggle 1 */}
            <div className='flex items-center  gap-[8px]'>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  value=''
                  className='sr-only peer'
                  checked={useWheelchair}
                  onChange={() => setUseWheelchair(!useWheelchair)}
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
              </label>
              <div>
                <p className='text-white text-[14px]'>Пользуюсь инвалидной или детской коляской</p>
                <p className='text-gray-400 text-[10px]'>Поможем избежать мест с трудной проходимостью</p>
              </div>
            </div>

            {/* Toggle 2 */}
            <div className='flex items-center  gap-[8px]'>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  value=''
                  className='sr-only peer'
                  checked={mentalHealthFeatures}
                  onChange={() => setMentalHealthFeatures(!mentalHealthFeatures)}
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
              </label>
              <div>
                <p className='text-white text-[14px]'>Есть особенности психического здоровья</p>
                <p className='text-gray-400 text-[10px]'>Поможем избежать мест с повышенным уровнем раздражителей</p>
              </div>
            </div>

            {/* Toggle 3 */}
            <div className='flex items-center  gap-[8px]'>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  value=''
                  className='sr-only peer'
                  checked={buildSafeRoutes}
                  onChange={() => setBuildSafeRoutes(!buildSafeRoutes)}
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
              </label>
              <div>
                <p className='text-white text-[14px]'>Хочу строить безопасные маршруты</p>
                <p className='text-gray-400 text-[10px]'>
                  Поможем избежать неосвещенных улиц и малолюдных мест в темное время суток
                </p>
              </div>
            </div>

            {/* Toggle 4 */}
            <div className='flex items-center  gap-[8px]'>
              <label className='relative inline-flex items-center cursor-pointer'>
                <input
                  type='checkbox'
                  value=''
                  className='sr-only peer'
                  checked={useRestroomsOften}
                  onChange={() => setUseRestroomsOften(!useRestroomsOften)}
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-green-600"></div>
              </label>
              <div>
                <p className='text-white text-[14px]'>Чаще пользуюсь уборными</p>
                <p className='text-gray-400 text-[10px]'>Поможем избежать мест с трудной проходимостью</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
