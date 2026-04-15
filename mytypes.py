"""Type aliases for use as type annotations within this project

Created 7 Mar 2023 by Greg Vance
"""

from scipy import optimize


type Choices = list[str | None]
type Result = optimize.OptimizeResult
