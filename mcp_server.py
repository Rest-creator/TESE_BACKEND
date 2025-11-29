# mcp_server.py
import os
import django
import sys
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDay

# ---------------------------------------------------------
# 1. SETUP DJANGO ENVIRONMENT
# ---------------------------------------------------------
# This allows us to use your models (Order, Listing, etc.) 
# inside this standalone script.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teseapp.settings')
django.setup()

# Now we can import your models
from products.models import Listing
from payment.models import Order
from search.models import QueryLog
from teseapi.models import User

# ---------------------------------------------------------
# 2. SETUP MCP SERVER
# ---------------------------------------------------------
from mcp.server.fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("Tese Marketplace Admin")

# ---------------------------------------------------------
# 3. DEFINE ANALYTICS TOOLS
# ---------------------------------------------------------

@mcp.tool()
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

@mcp.tool()
def analyze_search_trends(limit: int = 20) -> str:
    """
    Reviews what users are searching for (from QueryLog).
    Helps identify demand for products we might not have.
    """
    # Get recent queries, excluding null users if you want, or all
    logs = QueryLog.objects.order_by('-timestamp')[:limit]
    
    if not logs:
        return "No search logs available."

    # specialized logic: count distinct terms
    term_counts = {}
    for log in logs:
        term = log.query_text.lower().strip()
        term_counts[term] = term_counts.get(term, 0) + 1
    
    # Sort by frequency
    sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
    
    report = ["Top Recent Search Terms:"]
    for term, count in sorted_terms:
        report.append(f"- '{term}': searched {count} times")
        
    return "\n".join(report)

@mcp.tool()
def inventory_health_check() -> str:
    """
    Analyzes current listings. Returns breakdown by category,
    status (active/inactive), and average prices.
    """
    # 1. Category Breakdown
    cat_stats = Listing.objects.values('category').annotate(
        count=Count('id'),
        avg_price=Avg('price')
    ).order_by('-count')

    # 2. Status Breakdown
    status_stats = Listing.objects.values('status').annotate(count=Count('id'))

    report = ["--- INVENTORY HEALTH REPORT ---"]
    
    report.append("\nBy Category:")
    for cat in cat_stats:
        c_name = cat['category'] if cat['category'] else "Uncategorized"
        report.append(f"- {c_name}: {cat['count']} items (Avg Price: ${cat['avg_price']:.2f})")

    report.append("\nBy Status:")
    for stat in status_stats:
        report.append(f"- {stat['status']}: {stat['count']} items")

    return "\n".join(report)

@mcp.tool()
def get_user_demographics() -> str:
    """
    Analyzes user locations and account types (service vs standard).
    """
    # Location stats
    loc_stats = User.objects.values('location').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Service Type stats (e.g. are they farmers, logistics, etc?)
    service_stats = User.objects.values('service_type').annotate(count=Count('id'))

    report = ["--- USER DEMOGRAPHICS ---"]
    report.append("\nTop Locations:")
    for loc in loc_stats:
        l_name = loc['location'] if loc['location'] else "Unknown"
        report.append(f"- {l_name}: {loc['count']} users")
        
    report.append("\nService Types:")
    for srv in service_stats:
        s_name = srv['service_type'] if srv['service_type'] else "Standard User"
        report.append(f"- {s_name}: {srv['count']}")
        
    return "\n".join(report)

# ---------------------------------------------------------
# 4. RUN SERVER
# ---------------------------------------------------------
if __name__ == "__main__":
    mcp.run()