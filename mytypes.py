"""Type aliases for use as type annotations within this project

Created 7 Mar 2023 by Greg Vance
"""

from typing import List, Union

import numpy as np
from scipy import optimize


Array = np.ndarray
Choices = Union[List[str], List[None], List[Union[str, None]]]
Result = optimize.OptimizeResult
