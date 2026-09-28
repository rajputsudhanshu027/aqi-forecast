import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error


def regression_metrics(
    y_true,
    y_pred,
) -> dict[str, float]:
    mae = mean_absolute_error(y_true, y_pred)

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred,
        )
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
    }
