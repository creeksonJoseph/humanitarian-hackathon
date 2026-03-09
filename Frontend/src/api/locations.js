import apiClient from './api';

export const fetchLocations = async () => {
    const response = await apiClient.get(`/locations`);
    return response.data;
};
