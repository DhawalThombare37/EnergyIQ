"""
Model Engine Module — xgboost 3.x + sklearn 1.5 compatible
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb

HOUSEHOLD_UNITS_PARAMS  = {'colsample_bytree': 0.7, 'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 200, 'subsample': 0.8}
HOUSEHOLD_BILL_PARAMS   = {'colsample_bytree': 0.7, 'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 200, 'subsample': 0.7}
INDUSTRIAL_UNITS_PARAMS = {'colsample_bytree': 0.8, 'learning_rate': 0.1, 'max_depth': 3, 'n_estimators': 100, 'subsample': 0.7}
INDUSTRIAL_BILL_PARAMS  = {'colsample_bytree': 0.8, 'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 100, 'subsample': 0.7}

CAND_HOUSE_BASE = [
    'Global_active_power', 'Global_reactive_power', 'Voltage',
    'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3', 'records_count',
    'day_of_year_sin', 'day_of_year_cos', 'day_of_week', 'month', 'year', 'festival_flag',
    'daily_energy_kwh_lag1', 'daily_energy_kwh_lag2', 'daily_energy_kwh_lag3',
]
CAND_IND_BASE = [
    'Global_active_power', 'Global_reactive_power', 'Global_intensity',
    'Sub_metering_3', 'Voltage', 'records_count',
    'day_of_year_sin', 'day_of_year_cos', 'day_of_week', 'month', 'year', 'festival_flag',
    'daily_energy_kwh_lag1', 'daily_energy_kwh_lag2', 'daily_energy_kwh_lag3',
]
ROLLING_COLS = [
    'Global_active_power', 'Global_reactive_power', 'Voltage', 'Global_intensity',
    'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3'
]
CAT_CANDIDATES = ['Season_mode', 'DayOfWeek_mode', 'Tariff_Time_Slot_Daily_mode']


def build_preprocessor(num_features, cat_features):
    transformers = []
    if num_features:
        transformers.append(('num', StandardScaler(), num_features))
    if cat_features:
        transformers.append(('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_features))
    if not transformers:
        return None
    return ColumnTransformer(transformers=transformers, remainder='drop')


def mape_pct(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask = np.abs(y_true) > 1e-6
    if mask.sum() == 0:
        return 0.0
    return float(mean_absolute_percentage_error(y_true[mask], y_pred[mask]) * 100.0)


def _build_feature_list(base_cands, daily_cols):
    feats = []
    seen = set()
    for c in base_cands:
        if c in daily_cols and c not in seen:
            feats.append(c)
            seen.add(c)
    for col in ROLLING_COLS:
        for suffix in ('_rollmean3', '_rollstd3'):
            f = col + suffix
            if f in daily_cols and f not in seen:
                feats.append(f)
                seen.add(f)
    for c in CAT_CANDIDATES:
        if c in daily_cols and c not in seen:
            feats.append(c)
            seen.add(c)
    return feats


def _train_xgb(Xtr, ytr, Xte, params):
    model = xgb.XGBRegressor(
        **params,
        objective='reg:squarederror',
        random_state=42,
        verbosity=0,
    )
    model.fit(Xtr, ytr, verbose=False)
    return model, model.predict(Xte)


def run_predictions(daily: pd.DataFrame, train_days: int = 150, pred_days: int = 30):
    daily = daily.sort_values('date').reset_index(drop=True)
    total = len(daily)

    if train_days + pred_days > total:
        train_days = max(1, int(total * 0.8))
        pred_days  = max(1, total - train_days)

    train_df = daily.iloc[:train_days].copy()
    test_df  = daily.iloc[train_days:train_days + pred_days].copy()
    if len(test_df) == 0:
        raise ValueError("Not enough data for the requested train/test split.")

    cols = daily.columns.tolist()
    house_feats = _build_feature_list(CAND_HOUSE_BASE, cols)
    ind_feats   = _build_feature_list(CAND_IND_BASE,   cols)

    house_num = [c for c in house_feats if not c.endswith('_mode')]
    house_cat = [c for c in house_feats if c.endswith('_mode')]
    ind_num   = [c for c in ind_feats   if not c.endswith('_mode')]
    ind_cat   = [c for c in ind_feats   if c.endswith('_mode')]

    y_tr_units = train_df['daily_energy_kwh'].values
    y_te_units = test_df['daily_energy_kwh'].values
    y_tr_slab  = train_df['daily_bill_slab'].values
    y_te_slab  = test_df['daily_bill_slab'].values
    y_tr_tou   = train_df['daily_bill_tou'].values
    y_te_tou   = test_df['daily_bill_tou'].values

    # Household pipeline
    pre_h = build_preprocessor(house_num, house_cat)
    if pre_h is None:
        raise ValueError("No valid features found for household model.")
    Xh_tr = pre_h.fit_transform(train_df)
    Xh_te = pre_h.transform(test_df)

    h_unit_model, h_unit_pred = _train_xgb(Xh_tr, y_tr_units, Xh_te, HOUSEHOLD_UNITS_PARAMS)
    h_bill_model, h_bill_pred = _train_xgb(Xh_tr, y_tr_slab,  Xh_te, HOUSEHOLD_BILL_PARAMS)

    # Industrial pipeline
    pre_i = build_preprocessor(ind_num, ind_cat)
    if pre_i is None:
        raise ValueError("No valid features found for industrial model.")
    Xi_tr = pre_i.fit_transform(train_df)
    Xi_te = pre_i.transform(test_df)

    i_unit_model, i_unit_pred = _train_xgb(Xi_tr, y_tr_units, Xi_te, INDUSTRIAL_UNITS_PARAMS)
    i_bill_model, i_bill_pred = _train_xgb(Xi_tr, y_tr_tou,   Xi_te, INDUSTRIAL_BILL_PARAMS)

    dates = test_df['date'].dt.strftime('%Y-%m-%d').tolist()

    return {
        'dates':         dates,
        'test_df':       test_df,
        'train_days':    train_days,
        'pred_days':     len(test_df),
        'h_unit_actual': y_te_units,
        'h_unit_pred':   h_unit_pred,
        'h_bill_actual': y_te_slab,
        'h_bill_pred':   h_bill_pred,
        'h_unit_mape':   mape_pct(y_te_units, h_unit_pred),
        'h_bill_mape':   mape_pct(y_te_slab,  h_bill_pred),
        'i_unit_actual': y_te_units,
        'i_unit_pred':   i_unit_pred,
        'i_bill_actual': y_te_tou,
        'i_bill_pred':   i_bill_pred,
        'i_unit_mape':   mape_pct(y_te_units, i_unit_pred),
        'i_bill_mape':   mape_pct(y_te_tou,   i_bill_pred),
        'h_unit_model':  h_unit_model,
        'i_unit_model':  i_unit_model,
        'house_feats_num': house_num,
        'ind_feats_num':   ind_num,
    }
