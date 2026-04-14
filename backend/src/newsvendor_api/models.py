from pydantic import BaseModel, Field, model_validator


class SimulationRequest(BaseModel):
    purchase_cost: float = Field(default=0.25, gt=0, description="Unit purchase cost")
    resale_value: float = Field(default=1.0, gt=0, description="Unit resale price")
    average_demand: float = Field(default=150.0, ge=0, description="Expected demand")
    uniform_plus_minus: float = Field(
        default=30.0,
        ge=0,
        description="Half-width of the uniform demand distribution",
    )
    repetitions: int = Field(
        default=5000,
        ge=100,
        le=250000,
        description="Number of Monte Carlo replications",
    )
    search_lower_quantity: float = Field(
        default=100.0,
        ge=0,
        description="Lower bound for the order quantity grid search",
    )
    search_upper_quantity: float = Field(
        default=220.0,
        ge=0,
        description="Upper bound for the order quantity grid search",
    )
    search_step: float = Field(
        default=5.0,
        gt=0,
        description="Step size for the order quantity grid search",
    )
    seed: int | None = Field(default=None, description="Optional seed for reproducibility")

    @model_validator(mode="after")
    def validate_search_window(self) -> "SimulationRequest":
        if self.search_upper_quantity < self.search_lower_quantity:
            raise ValueError("search_upper_quantity must be greater than or equal to search_lower_quantity")

        grid_points = int(((self.search_upper_quantity - self.search_lower_quantity) / self.search_step) + 1)
        if grid_points > 1000:
            raise ValueError("search grid is too dense; reduce the range or increase the step size")

        return self
