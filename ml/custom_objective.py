"""
Custom objective functions for LightGBM.
"""

import numpy as np


def asymmetric_l2_objective(y_pred, y_true):
    """
    Asymmetric L2 loss objective function for LightGBM.
    
    Penalizes underestimates more than overestimates to reduce stockout risk.
    - Underestimates (y_pred < y_true): 2x penalty
    - Overestimates (y_pred >= y_true): 1x penalty
    
    Args:
        y_pred: Predicted values (1D array)
        y_true: True values (LightGBM Dataset with .get_label() method)
    
    Returns:
        grad: Gradient (1D array)
        hess: Hessian (1D array)
    """
    # Extract true values
    if hasattr(y_true, 'get_label'):
        y_true = y_true.get_label()
    
    y_true = np.array(y_true, dtype=np.float32)
    y_pred = np.array(y_pred, dtype=np.float32).reshape(-1)
    
    # Calculate residuals
    residuals = y_pred - y_true
    
    # Determine which are underestimates vs overestimates
    is_underestimate = residuals < 0
    
    # Asymmetric penalty: underestimates get 2x penalty
    penalty = np.where(is_underestimate, 2.0, 1.0)
    
    # Gradient: d/dy_pred of (penalty * (y_pred - y_true)^2)
    # = 2 * penalty * (y_pred - y_true)
    grad = 2.0 * penalty * residuals
    
    # Hessian: d^2/dy_pred^2 = 2 * penalty (constant)
    hess = 2.0 * penalty * np.ones_like(residuals)
    
    return grad, hess
