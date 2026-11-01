import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const fetchHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.data;
  } catch (error) {
    console.error('Error fetching health check:', error);
    throw error;
  }
};

export const uploadDataset = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/dataset/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDatasetSummary = async () => {
  const response = await api.get('/dataset/summary');
  return response.data;
};

export const updateColumnMappings = async (mappings) => {
  const response = await api.post('/dataset/map', { mappings });
  return response.data;
};

export const cleanDataset = async () => {
  const response = await api.post('/dataset/clean');
  return response.data;
};

export const loadSampleDataset = async () => {
  const response = await api.post('/dataset/load-sample');
  return response.data;
};

export const getCleanedDownloadUrl = () => '/api/dataset/download/cleaned';
export const getRawDownloadUrl = () => '/api/dataset/download/raw';

export const getSalesSummary = async () => {
  const response = await api.get('/analysis/summary');
  return response.data;
};

export const getMonthlySales = async () => {
  const response = await api.get('/analysis/monthly');
  return response.data;
};

export const getProductSales = async () => {
  const response = await api.get('/analysis/products');
  return response.data;
};

export const getCategorySales = async () => {
  const response = await api.get('/analysis/categories');
  return response.data;
};

export const getStoreSales = async () => {
  const response = await api.get('/analysis/stores');
  return response.data;
};

export const getProducts = async () => {
  const response = await api.get('/products');
  return response.data;
};

// --- Milestone 5: Feature Engineering ---

export const generateFeatures = async () => {
  const response = await api.post('/model/features/generate');
  return response.data;
};

export const getFeaturesStatus = async () => {
  const response = await api.get('/model/features/status');
  return response.data;
};

export const getFeaturesPreview = async () => {
  const response = await api.get('/model/features/preview');
  return response.data;
};

// --- Milestone 6: Model Training ---

export const trainModels = async () => {
  const response = await api.post('/model/train');
  return response.data;
};

export const getModelTrainingStatus = async () => {
  const response = await api.get('/model/training-status');
  return response.data;
};

export const getModelResults = async () => {
  const response = await api.get('/model/results');
  return response.data;
};

// --- Milestone 7: Model Evaluation & Comparison ---

export const evaluateModels = async (force = false) => {
  const response = await api.post(`/model/evaluate?force=${force}`);
  return response.data;
};

export const getModelEvaluation = async () => {
  const response = await api.get('/model/evaluation');
  return response.data;
};

export const getModelEvaluationStatus = async () => {
  const response = await api.get('/model/evaluation/status');
  return response.data;
};

// --- Milestone 8: Demand Forecasting ---

export const getForecastOptions = async () => {
  const response = await api.get('/forecast/options');
  return response.data;
};

export const generateForecast = async (params) => {
  const response = await api.post('/forecast/generate', params);
  return response.data;
};

// --- Milestone 9: Inventory Simulation ---

export const simulateInventory = async (params) => {
  const response = await api.post('/inventory/simulate', params);
  return response.data;
};

export const getInventoryStockInfo = async (storeId, productId) => {
  const response = await api.get('/inventory/stock-info', {
    params: { store_id: storeId, product_id: productId }
  });
  return response.data;
};

// Backward-compatibility alias
export const analyzeInventory = simulateInventory;

export default api;
