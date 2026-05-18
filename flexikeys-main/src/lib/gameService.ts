import api from './apiClient';

export const getLevels = async () => {
  const response = await api.get('/levels/'); // Эндпоинт из твоего Django urls.py
  return response.data;
};

export const saveScore = async (scoreData: { level_id: number; points: number }) => {
  const response = await api.post('/scores/', scoreData);
  return response.data;
};