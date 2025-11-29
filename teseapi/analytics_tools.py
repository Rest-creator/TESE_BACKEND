# teseapi/analytics_tools.py
from django.utils import timezone
from datetime import timedelta
from products.models import Order
from django.db.models import Sum
from django.db.models import Count
from django.db.models.functions import TruncDay

# This is the exact same logic, just in a standard Django file
def get_sales_revenue_trend(days: int = 30) -> str:
    """
    Analyzes total revenue and order volume over the last X days.
    Useful for seeing financial performance.
    """
    start_date = timezone.now() - timedelta(days=days)
    
    # Filter for PAID orders only
    orders = Order.objects.filter(
        created_at__gte=start_date, 
        status='PAID'
    ).annotate(day=TruncDay('created_at')).values('day').annotate(
        daily_revenue=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('day')

    if not orders:
        return "No paid orders found in this period."

    report = [f"Sales Report (Last {days} Days):"]
    total_rev = 0
    
    for entry in orders:
        date_str = entry['day'].strftime('%Y-%m-%d')
        rev = entry['daily_revenue']
        count = entry['order_count']
        total_rev += rev
        report.append(f"- {date_str}: ${rev} ({count} orders)")
        
    report.append(f"\nTOTAL PERIOD REVENUE: ${total_rev}")
    return "\n".join(report)

# Define the Tool Schema (So the AI knows how to use it)
tools_schema = [
    {
        "name": "get_sales_revenue_trend",
        "description": "Get sales revenue trend for the last X days",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days to look back"}
            },
            "required": ["days"]
        }
    }
]