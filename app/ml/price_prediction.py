import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
import joblib
import os
import logging

logger = logging.getLogger(__name__)


class PricePredictionModel:
    """LSTM/GRU based price prediction model"""

    def __init__(
        self,
        model_type: str = 'lstm',
        sequence_length: int = 60,
        model_path: str = './models'
    ):
        self.model_type = model_type  # 'lstm' or 'gru'
        self.sequence_length = sequence_length
        self.model_path = model_path
        self.model: Optional[keras.Model] = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.feature_scaler = MinMaxScaler(feature_range=(0, 1))

        os.makedirs(model_path, exist_ok=True)

    def prepare_data(
        self,
        df: pd.DataFrame,
        features: list = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare data for training"""
        if features is None:
            features = ['close', 'volume', 'high', 'low', 'open']

        # Extract features
        data = df[features].values

        # Scale the data
        scaled_data = self.feature_scaler.fit_transform(data)

        # Create sequences
        X, y = [], []

        for i in range(self.sequence_length, len(scaled_data)):
            X.append(scaled_data[i - self.sequence_length:i])
            y.append(scaled_data[i, 0])  # Predict close price

        X, y = np.array(X), np.array(y)

        # Train-test split (80-20)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        return X_train, X_test, y_train, y_test

    def build_lstm_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """Build LSTM model"""
        model = Sequential([
            LSTM(units=128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            BatchNormalization(),

            LSTM(units=64, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),

            LSTM(units=32, return_sequences=False),
            Dropout(0.2),
            BatchNormalization(),

            Dense(units=16, activation='relu'),
            Dropout(0.1),

            Dense(units=1)
        ])

        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )

        return model

    def build_gru_model(self, input_shape: Tuple[int, int]) -> keras.Model:
        """Build GRU model"""
        model = Sequential([
            GRU(units=128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            BatchNormalization(),

            GRU(units=64, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),

            GRU(units=32, return_sequences=False),
            Dropout(0.2),
            BatchNormalization(),

            Dense(units=16, activation='relu'),
            Dropout(0.1),

            Dense(units=1)
        ])

        model.compile(
            optimizer='adam',
            loss='mean_squared_error',
            metrics=['mae']
        )

        return model

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """Train the model"""
        input_shape = (X_train.shape[1], X_train.shape[2])

        if self.model_type == 'lstm':
            self.model = self.build_lstm_model(input_shape)
        else:
            self.model = self.build_gru_model(input_shape)

        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        model_checkpoint = ModelCheckpoint(
            os.path.join(self.model_path, f'{self.model_type}_best.h5'),
            monitor='val_loss',
            save_best_only=True
        )

        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_test, y_test),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[early_stopping, model_checkpoint],
            verbose=1
        )

        # Evaluate
        test_loss, test_mae = self.model.evaluate(X_test, y_test, verbose=0)

        logger.info(f"Model training completed. Test Loss: {test_loss}, Test MAE: {test_mae}")

        return {
            'history': history.history,
            'test_loss': test_loss,
            'test_mae': test_mae
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        predictions = self.model.predict(X)
        return predictions

    def predict_next_price(self, recent_data: pd.DataFrame, features: list = None) -> Dict[str, float]:
        """Predict next price based on recent data"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        if features is None:
            features = ['close', 'volume', 'high', 'low', 'open']

        # Prepare input sequence
        data = recent_data[features].tail(self.sequence_length).values
        scaled_data = self.feature_scaler.transform(data)
        X = scaled_data.reshape(1, self.sequence_length, len(features))

        # Predict
        prediction = self.model.predict(X, verbose=0)

        # Inverse transform to get actual price
        # Create dummy array with same shape as training data
        dummy = np.zeros((1, len(features)))
        dummy[0, 0] = prediction[0, 0]
        predicted_price = self.feature_scaler.inverse_transform(dummy)[0, 0]

        current_price = recent_data['close'].iloc[-1]
        predicted_change = ((predicted_price - current_price) / current_price) * 100

        return {
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_change_percent': float(predicted_change),
            'direction': 'UP' if predicted_change > 0 else 'DOWN'
        }

    def save_model(self, symbol: str):
        """Save model and scaler"""
        if self.model is None:
            raise ValueError("No model to save")

        model_filename = os.path.join(self.model_path, f'{symbol}_{self.model_type}_model.h5')
        scaler_filename = os.path.join(self.model_path, f'{symbol}_{self.model_type}_scaler.pkl')

        self.model.save(model_filename)
        joblib.dump(self.feature_scaler, scaler_filename)

        logger.info(f"Model saved: {model_filename}")

    def load_model(self, symbol: str):
        """Load model and scaler"""
        model_filename = os.path.join(self.model_path, f'{symbol}_{self.model_type}_model.h5')
        scaler_filename = os.path.join(self.model_path, f'{symbol}_{self.model_type}_scaler.pkl')

        if not os.path.exists(model_filename):
            raise FileNotFoundError(f"Model file not found: {model_filename}")

        self.model = load_model(model_filename)
        self.feature_scaler = joblib.load(scaler_filename)

        logger.info(f"Model loaded: {model_filename}")

    def calculate_confidence(
        self,
        recent_data: pd.DataFrame,
        features: list = None,
        n_predictions: int = 10
    ) -> float:
        """Calculate prediction confidence based on consistency"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")

        predictions = []

        # Make multiple predictions with slight variations
        for _ in range(n_predictions):
            pred = self.predict_next_price(recent_data, features)
            predictions.append(pred['predicted_change_percent'])

        # Calculate standard deviation
        std_dev = np.std(predictions)
        mean_pred = np.mean(predictions)

        # Confidence based on consistency (lower std = higher confidence)
        # Normalize to 0-1 range
        confidence = max(0, 1 - (std_dev / (abs(mean_pred) + 1)))

        return float(confidence)


class EnsemblePricePredictor:
    """Ensemble of LSTM and GRU models for better predictions"""

    def __init__(self, sequence_length: int = 60, model_path: str = './models'):
        self.lstm_model = PricePredictionModel('lstm', sequence_length, model_path)
        self.gru_model = PricePredictionModel('gru', sequence_length, model_path)

    def train_ensemble(
        self,
        df: pd.DataFrame,
        features: list = None,
        epochs: int = 50
    ):
        """Train both models"""
        # Prepare data
        X_train, X_test, y_train, y_test = self.lstm_model.prepare_data(df, features)

        # Train LSTM
        logger.info("Training LSTM model...")
        lstm_results = self.lstm_model.train(X_train, y_train, X_test, y_test, epochs)

        # Prepare data for GRU
        X_train, X_test, y_train, y_test = self.gru_model.prepare_data(df, features)

        # Train GRU
        logger.info("Training GRU model...")
        gru_results = self.gru_model.train(X_train, y_train, X_test, y_test, epochs)

        return {
            'lstm': lstm_results,
            'gru': gru_results
        }

    def predict(self, recent_data: pd.DataFrame, features: list = None) -> Dict[str, Any]:
        """Get ensemble prediction (average of both models)"""
        lstm_pred = self.lstm_model.predict_next_price(recent_data, features)
        gru_pred = self.gru_model.predict_next_price(recent_data, features)

        # Average the predictions
        avg_predicted_price = (lstm_pred['predicted_price'] + gru_pred['predicted_price']) / 2
        current_price = recent_data['close'].iloc[-1]
        predicted_change = ((avg_predicted_price - current_price) / current_price) * 100

        # Calculate confidence
        lstm_confidence = self.lstm_model.calculate_confidence(recent_data, features)
        gru_confidence = self.gru_model.calculate_confidence(recent_data, features)
        avg_confidence = (lstm_confidence + gru_confidence) / 2

        return {
            'current_price': float(current_price),
            'predicted_price': float(avg_predicted_price),
            'predicted_change_percent': float(predicted_change),
            'direction': 'UP' if predicted_change > 0 else 'DOWN',
            'confidence': float(avg_confidence),
            'lstm_prediction': lstm_pred,
            'gru_prediction': gru_pred
        }

    def save_models(self, symbol: str):
        """Save both models"""
        self.lstm_model.save_model(symbol)
        self.gru_model.save_model(symbol)

    def load_models(self, symbol: str):
        """Load both models"""
        self.lstm_model.load_model(symbol)
        self.gru_model.load_model(symbol)