"""Type aliases for use as type annotations within this project

Created 7 Mar 2023 by Greg Vance
"""

import numpy as np
from scipy import optimize


type Array = np.ndarray
type Choices = list[str] | list[None] | list[str | None]
type Result = optimize.OptimizeResult
