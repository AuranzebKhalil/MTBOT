import joblib
import pandas as pd

try:
    model = joblib.load("models/rf_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    
    # Try to see if it's a CalibratedClassifierCV
    if hasattr(model, "estimator"): # CalibratedClassifierCV
        base_model = model.estimator
    else:
        base_model = model
        
    if hasattr(model, "calibrated_classifiers_") and len(model.calibrated_classifiers_) > 0:
        first_cal = model.calibrated_classifiers_[0]
        if hasattr(first_cal, "base_estimator"):
            clf = first_cal.base_estimator
            if hasattr(clf, "feature_names_in_"):
                print("Internal RF Features:", clf.feature_names_in_)
            else:
                print("Internal RF has no feature_names_in_")
        
    if hasattr(scaler, "feature_names_in_"):
        print("Scaler Features:", scaler.feature_names_in_)
except Exception as e:
    print("Error:", e)
