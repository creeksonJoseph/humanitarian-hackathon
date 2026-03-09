import apiClient from './api';

export const fetchRiders = async (tab = "all", location = "", search = "", page = 1, limit = 50) => {
    const params = { tab, page, limit };
    if (location) params.place = location;
    if (search) params.search = search;
    
    const response = await apiClient.get(`/riders`, { params });
    return response.data;
};

export const verifyRider = async (phone) => {
    const response = await apiClient.post(`/riders/${encodeURIComponent(phone)}/verify`);
    return response.data;
};
