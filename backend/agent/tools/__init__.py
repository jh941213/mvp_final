"""
KTDS 에이전트 전용 도구들
각 에이전트별로 특화된 도구들을 제공
"""

from .hr_tools import (
    get_salary_info, 
    get_vacation_info, 
    get_education_programs,
    get_employee_directory,
    get_welfare_benefits
)

from .bulletin_tools import (
    get_recent_announcements,
    get_company_events,
    get_club_activities,
    search_bulletin_posts,
    get_cafeteria_menu,
    get_shuttle_schedule
)

from .project_tools import (
    get_active_projects,
    get_project_details,
    get_team_workload,
    get_project_milestones,
    get_resource_allocation,
    get_project_risks,
    create_project_report
)

from .search_tools import (
    web_search,
    news_search,
    create_web_search_tool,
    create_news_search_tool,
    create_search_agent
)

__all__ = [
    # HR Tools
    "get_salary_info",
    "get_vacation_info", 
    "get_education_programs",
    "get_employee_directory",
    "get_welfare_benefits",
    
    # Bulletin Tools
    "get_recent_announcements",
    "get_company_events",
    "get_club_activities",
    "search_bulletin_posts",
    "get_cafeteria_menu",
    "get_shuttle_schedule",
    
    # Project Tools
    "get_active_projects",
    "get_project_details",
    "get_team_workload",
    "get_project_milestones",
    "get_resource_allocation",
    "get_project_risks",
    "create_project_report",
    
    # Search Tools
    "web_search",
    "news_search", 
    "create_web_search_tool",
    "create_news_search_tool",
    "create_search_agent"
] 