"""
Database cleanup script to fix corrupted time fields in CalendarEvent model.

Run this with: py manage.py shell
Then: exec(open('fix_calendar_times.py').read())
"""

from main.models import CalendarEvent

def fix_time_fields():
    """Fix all events with invalid time fields."""
    events = CalendarEvent.objects.all()
    fixed_count = 0
    
    for event in events:
        needs_save = False
        
        # Check and fix start_time
        if event.start_time is not None and isinstance(event.start_time, str):
            print(f"Event {event.id}: Invalid start_time type (str): {event.start_time}")
            event.start_time = None
            needs_save = True
        
        # Check and fix end_time  
        if event.end_time is not None and isinstance(event.end_time, str):
            print(f"Event {event.id}: Invalid end_time type (str): {event.end_time}")
            event.end_time = None
            needs_save = True
        
        if needs_save:
            event.save()
            fixed_count += 1
            print(f"  → Fixed event {event.id}")
    
    print(f"\nTotal events fixed: {fixed_count}")
    print("All calendar events have been cleaned up!")

if __name__ == '__main__':
    fix_time_fields()
