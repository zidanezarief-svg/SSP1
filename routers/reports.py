from fastapi import APIRouter, Query

router = APIRouter (
    prefix = "/reports",
    tags = ["Reports"]
)

@router.get("/monthly_sales")
def get_sales_report(year: int, 
                     month: int = Query(ge=1, le=12)):
    return {"message": "View monthly sales",
            "year" : year,
            "month" : month
}

@router.get("/monthly_costs")
def get_cost_report(year: int, 
                    month: int = Query(ge=1, le=12)):
    return {"message": "View total monthly cost",
            "year" : year,
            "month" : month 
}

@router.get("/monthly_profit")
def get_profit_report(year: int, 
                      month: int = Query(ge=1, le=12)):
    return {"message": "View total monthly profit",
            "year" : year,
            "month" : month
}

@router.get("/daily_sales")
def get_daily_sales():
    return {"message": "View daily sales"}

@router.get("/best_seller")
def get_best_sellers():
    return {"message": "View best selling products"}