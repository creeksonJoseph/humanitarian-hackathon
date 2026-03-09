import apiClient from './api';

export const fetchHazards = async (location = "", page = 1, limit = 50) => {
    const params = { page, limit };
    if (location) params.place = location;
    
    const response = await apiClient.get(`/hazards`, { params });
    return response.data; 
};

export const clearHazard = async (id) => {
    const response = await apiClient.post(`/hazards/${id}/clear`);
    return response.data;
};
