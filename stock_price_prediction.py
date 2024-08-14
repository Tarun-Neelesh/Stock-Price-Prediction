# -*- coding: utf-8 -*-
"""Stock Price Prediction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1DUyu3_u_0W6W78pvlCDlCgcxSQqh8YqS
"""

import numpy as np
import pandas as pd
import matplotlib.pylab as plt

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, LSTM, Conv1D, GRU
from tensorflow.keras.optimizers import Adam  # Use the standard Adam optimizer

from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import TimeSeriesSplit

class Timeseries:
    def __init__(self, data: pd.DataFrame, company: str):
        self.data = data
        self.company = company

    def prepare_data(self) -> pd.DataFrame:
        self.scaler = MinMaxScaler()
        df = self.data[self.data['Company'] == self.company]

        if df.empty:
            raise ValueError(f"No data found for company {self.company}")

        df = df.dropna()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df[['Date', 'Close']]  # Keep only 'Date' and 'Close' columns

        if df['Close'].isnull().all():
            raise ValueError("All 'Close' values are NaN after filtering.")

        df['Close'] = self.scaler.fit_transform(df[['Close']])
        return df

    def split_sequence(self, sequence: pd.Series, n_steps_in: int, n_steps_out: int):
        X, y = [], []
        for i in range(len(sequence)):
            end_ix = i + n_steps_in
            out_end_ix = end_ix + n_steps_out
            if out_end_ix > len(sequence):
                break
            X.append(sequence[i:end_ix])
            y.append(sequence[end_ix:out_end_ix])
        return np.array(X), np.array(y)

    def train_test_split(self, df: pd.DataFrame):
        train_size = int(len(df) * 0.7)
        train_df, test_df = df[:train_size], df[train_size:]
        return train_df, test_df

    def models(self, n_steps_in: int, n_steps_out: int, n_features: int):
        self.model_Conv1D = Sequential([
            Conv1D(64, 3, activation='relu', input_shape=(n_steps_in, n_features)),
            Conv1D(64, 3, activation='relu'),
            Flatten(),
            Dense(n_steps_out)
        ])
        self.model_Conv1D.compile(optimizer=Adam(learning_rate=0.0001), loss='mse', metrics=['accuracy'])

        self.model_GRU = Sequential([
            GRU(200, return_sequences=True, input_shape=(n_steps_in, n_features)),
            GRU(200, return_sequences=True),
            GRU(200, return_sequences=True),
            GRU(200),
            Dense(n_steps_out)
        ])
        self.model_GRU.compile(optimizer=Adam(learning_rate=0.0001), loss='mse', metrics=['accuracy'])

        self.model_LSTM = Sequential([
            LSTM(200, return_sequences=True, input_shape=(n_steps_in, n_features)),
            LSTM(200, return_sequences=True),
            LSTM(200, return_sequences=True),
            LSTM(200),
            Dense(n_steps_out)
        ])
        self.model_LSTM.compile(optimizer=Adam(learning_rate=0.0001), loss='mse', metrics=['accuracy'])

    def train_models(self, X_train: np.array, y_train: np.array):
        scores_LSTM, scores_Conv1D, scores_GRU = [], [], []
        timefold = TimeSeriesSplit(n_splits=10).split(X_train, y_train)

        for k, (train_idx, test_idx) in enumerate(timefold):
            self.model_LSTM.fit(X_train[train_idx], y_train[train_idx], epochs=50, verbose=0, validation_split=0.3)
            score_LSTM = self.model_LSTM.evaluate(X_train[test_idx], y_train[test_idx], verbose=0)
            scores_LSTM.append(score_LSTM)
            print(f'LSTM - Fold: {k+1}, Acc.: {score_LSTM[1]:.3f}, Loss: {score_LSTM[0]:.3f}')

            self.model_Conv1D.fit(X_train[train_idx], y_train[train_idx], epochs=50, verbose=0, validation_split=0.3)
            score_Conv1D = self.model_Conv1D.evaluate(X_train[test_idx], y_train[test_idx], verbose=0)
            scores_Conv1D.append(score_Conv1D)
            print(f'Conv1D - Fold: {k+1}, Acc.: {score_Conv1D[1]:.3f}, Loss: {score_Conv1D[0]:.3f}')

            self.model_GRU.fit(X_train[train_idx], y_train[train_idx], epochs=50, verbose=0, validation_split=0.3)
            score_GRU = self.model_GRU.evaluate(X_train[test_idx], y_train[test_idx], verbose=0)
            scores_GRU.append(score_GRU)
            print(f'GRU - Fold: {k+1}, Acc.: {score_GRU[1]:.4f}, Loss: {score_GRU[0]:.4f}')

    def test_prediction(self, x_input: np.array, df: pd.DataFrame):
        yhat_LSTM = self.model_LSTM.predict(x_input, verbose=0)
        yhat_Conv1D = self.model_Conv1D.predict(x_input, verbose=0)
        yhat_GRU = self.model_GRU.predict(x_input, verbose=0)

        mean_LSTM = self.scaler.inverse_transform(np.mean(yhat_LSTM, axis=1).reshape(-1, 1)).flatten()
        mean_Conv1D = self.scaler.inverse_transform(np.mean(yhat_Conv1D, axis=1).reshape(-1, 1)).flatten()
        mean_GRU = self.scaler.inverse_transform(np.mean(yhat_GRU, axis=1).reshape(-1, 1)).flatten()

        df['Close'] = self.scaler.inverse_transform(df['Close'].values.reshape(-1, 1)).flatten()
        return mean_LSTM, mean_Conv1D, mean_GRU, df

    def figure(self, df: pd.DataFrame, test_df: pd.DataFrame, LSTM: np.array, Conv1D: np.array, GRU: np.array, n_steps_in: int):
        plt.figure(figsize=(12, 6))
        plt.plot(df['Date'], df['Close'], '--b', label=self.company)
        plt.plot(test_df['Date'].iloc[n_steps_in:], LSTM, 'r', label='RNN using LSTM')
        plt.plot(test_df['Date'].iloc[n_steps_in:], Conv1D, 'k', label='Conv1D')
        plt.plot(test_df['Date'].iloc[n_steps_in:], GRU, 'g', label='GRU')
        plt.legend()
        plt.xlabel('Time')
        plt.ylabel('Close')
        plt.show()

def main():
    n_steps_in, n_steps_out, n_features = 5, 1, 1

    df = pd.read_csv('stock_details_5_years.csv')

    print('\nCompany: NIKE\n')
    NIKE = Timeseries(df, 'NKE')

    df_NIKE = NIKE.prepare_data()
    train_df_NIKE, test_df_NIKE = NIKE.train_test_split(df_NIKE)

    X_train_NIKE, y_train_NIKE = NIKE.split_sequence(train_df_NIKE['Close'], n_steps_in, n_steps_out)
    X_test_NIKE, y_test_NIKE = NIKE.split_sequence(test_df_NIKE['Close'], n_steps_in, n_steps_out)

    X_train_NIKE = X_train_NIKE.reshape((X_train_NIKE.shape[0], X_train_NIKE.shape[1], n_features))
    x_input_NIKE = X_test_NIKE.reshape((X_test_NIKE.shape[0], X_test_NIKE.shape[1], n_features))

    NIKE.models(n_steps_in, n_steps_out, n_features)
    NIKE.train_models(X_train_NIKE, y_train_NIKE)

    mean_LSTM, mean_Conv1D, mean_GRU, df = NIKE.test_prediction(x_input_NIKE, df_NIKE)

    NIKE.figure(df, test_df_NIKE, mean_LSTM, mean_Conv1D, mean_GRU, n_steps_in)

if __name__ == "__main__":
    main()