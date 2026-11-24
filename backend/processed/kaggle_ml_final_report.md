# ZeroWasteNet - Final ML Pipeline Report

## 1. Dataset Description

- Cleaned grocery records: 30400
- Feature-engineered records: 29840
- Unique stores: 5
- Unique products: 18
- Store-product combinations: 40
- Dataset date range: 2022-01-01 to 2024-01-30


## 2. Data Validation

- Total validation checks: 8
- Passed: 8
- Failed: 0


### Validation Check Results

| validation_check                     | status   | details                       |
|:-------------------------------------|:---------|:------------------------------|
| Total records                        | PASS     | 30400 records found           |
| Missing values                       | PASS     | 0 missing values              |
| Date validity                        | PASS     | 0 invalid dates               |
| Duplicate store-product-date records | PASS     | 0 duplicate records           |
| Store-product combinations           | PASS     | 40 unique combinations        |
| Date continuity                      | PASS     | 0 missing store-product dates |
| Negative sales quantities            | PASS     | 0 negative values             |
| Negative inventory values            | PASS     | 0 negative values             |

## 3. Feature Engineering


The feature-engineering pipeline created historical sales,
calendar and inventory-related input features.

**Numerical features:**
- day_of_week
- month
- is_weekend
- lag_1
- lag_7
- lag_14
- rolling_mean_7
- rolling_mean_14
- inventory_level
- discount
- price
- competitor_pricing

**Categorical features:**
- store_id
- product_id
- weather_condition
- promotion
- seasonality
- epidemic

**Prediction target:** quantity_sold


## 4. Model Training


**Selected model:** Random Forest Regressor V3

**Configuration:**
- Number of estimators: 300
- Maximum depth: 15
- Minimum samples per leaf: 2
- Random state: 42
- OneHotEncoder with handle_unknown='ignore'
- Chronological training and testing split

The model was trained using a scikit-learn Pipeline
containing preprocessing and Random Forest regression.


## 5. Fixed-Model Holdout Evaluation

Existing holdout evaluation results:


| model                  |     MAE |    RMSE |      R2 |
|:-----------------------|--------:|--------:|--------:|
| Random Forest V3       | 24.4302 | 32.2831 |  0.441  |
| Seasonal Naive (lag_7) | 46.0333 | 59.198  | -0.8795 |

## 6. Fixed-Model Seven-Day Backtest

- Total forecast records: 5880
- V3 MAE: 38.4057
- V3 RMSE: 49.8240
- Seasonal-naive MAE: 46.0757
- Seasonal-naive RMSE: 59.2856


## 7. Rolling-Origin Validation

- Total forecast records: 5880
- Forecast origins: 21


### Overall Model Metrics

| model             |     MAE |    RMSE |        R2 |
|:------------------|--------:|--------:|----------:|
| V3 Rolling-Origin | 38.3432 | 49.7942 | -0.326116 |
| Seasonal Naive    | 46.0757 | 59.2856 | -0.879842 |

### Day-wise Model Metrics

|   forecast_day |   v3_mae |   naive_mae |   v3_rmse |   naive_rmse |   records |
|---------------:|---------:|------------:|----------:|-------------:|----------:|
|              1 |  37.3346 |     46.4798 |   49.0472 |      60.3346 |       840 |
|              2 |  38.3678 |     46.4298 |   50.481  |      59.7182 |       840 |
|              3 |  37.6412 |     45.8893 |   49.209  |      59.6273 |       840 |
|              4 |  38.1633 |     45.7274 |   49.862  |      58.8494 |       840 |
|              5 |  38.6112 |     45.5964 |   49.8538 |      58.4457 |       840 |
|              6 |  38.5789 |     45.3976 |   50.0035 |      58.7693 |       840 |
|              7 |  39.7051 |     47.0095 |   50.0879 |      59.2328 |       840 |

## 8. Store-Product Performance Analysis

- Total combinations analysed: 40


### Highest Forecasting Errors

| store_id   | product_id   |     MAE |    RMSE |   Records |   MAE_Rank |
|:-----------|:-------------|--------:|--------:|----------:|-----------:|
| S005       | P0009        | 52.0031 | 64.3491 |       147 |          1 |
| S002       | P0011        | 48.5761 | 63.2192 |       147 |          2 |
| S004       | P0001        | 46.0678 | 60.9784 |       147 |          3 |
| S004       | P0010        | 45.7841 | 56.0101 |       147 |          4 |
| S003       | P0004        | 45.7212 | 57.7255 |       147 |          5 |
| S003       | P0015        | 45.5716 | 58.0723 |       147 |          6 |
| S004       | P0004        | 44.2561 | 56.5861 |       147 |          7 |
| S005       | P0010        | 43.5298 | 56.7281 |       147 |          8 |
| S004       | P0007        | 43.4375 | 54.3298 |       147 |          9 |
| S003       | P0014        | 42.7571 | 52.6529 |       147 |         10 |

- Best-performing combination: S003 / P0010 (MAE: 25.0328)

- Highest-error combination: S005 / P0009 (MAE: 52.0031)


## 9. Forecasting Methodology


The seven-day forecast uses recursive prediction.

At each forecast step:
1. The model predicts the next day's demand.
2. The predicted value is appended to the sales history.
3. Lag and rolling features are updated.
4. The next day's prediction uses the updated history.

The rolling-origin experiment retrains a separate model
at each forecast origin using historical data available
up to that origin.

The seasonal-naive baseline independently uses the
corresponding previous-week sales value.


## 10. Limitations


1. The source dataset ends on 2024-01-30. The forecasts
   are historical experiments, not live 2026 forecasts.

2. Future external variables such as inventory, price,
   promotions and weather are held at their latest
   known values during the recursive forecast.

3. The target quantity_sold may be affected by stockouts,
   so it may not represent unconstrained customer demand.

4. The rolling-origin evaluation has negative R².
   Although V3 outperforms the seasonal-naive baseline
   on MAE and RMSE, forecasting errors remain substantial.

5. Model performance varies between store-product
   combinations.

6. The evaluation uses historical data and does not
   establish real-world operational performance.


## 11. Conclusion


The project implemented a complete baseline ML workflow
covering data preprocessing, data validation, feature
engineering, Random Forest training, model evaluation
and recursive seven-day forecasting.

The selected V3 model outperformed the seasonal-naive
baseline on MAE and RMSE in the rolling-origin experiment.

The generated forecasts and evaluation reports provide
a foundation for integrating demand estimates into
expiry monitoring, surplus inventory detection and
grocery redistribution workflows.

Further work is required to improve forecasting accuracy
and validate the system using operational data and
realistic future input variables.
