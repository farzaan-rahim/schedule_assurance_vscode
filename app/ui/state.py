from dataclasses import dataclass,field
from typing import Any

NAVIGATION=(('Overview','space_dashboard'),('Projects','folder_open'),('Schedule Versions','layers'),
    ('Schedule Health','monitor_heart'),('DCMA','fact_check'),('Change Analysis','compare_arrows'),
    ('Milestones','flag'),('CPM / Paths','account_tree'),('Diagnostics','warning_amber'),('Reports','download'))

@dataclass(frozen=True)
class TableQuery:
    search: str=''
    wbs: str=''
    status: str=''
    activity_type: str=''
    classification: str=''
    severity: str=''
    category: str=''
    offset: int=0
    limit: int=50
    sort: str=''
    descending: bool=False
    def __post_init__(self):
        if self.offset<0 or not 1<=self.limit<=200:raise ValueError('Use offset >= 0 and page sizes from 1 to 200.')

@dataclass
class SessionState:
    page: str='Overview'
    project_id: Any=None
    version_id: Any=None
    source_version_id: Any=None
    target_version_id: Any=None
    analysis_anchor_id: str | None=None
    analysis_anchor_code: str | None=None
    global_search: str=''
    analysis_mode: str='CALIBRATION'
    required_finish: str=''
    filters: dict=field(default_factory=dict)
    busy: bool=False
    def select_project(self,key):
        if key!=self.project_id:
            self.project_id=key;self.version_id=None;self.source_version_id=None;self.target_version_id=None
            self.analysis_anchor_id=None;self.analysis_anchor_code=None;self.global_search='';self.filters.clear()
    def select_version(self,key):
        if key!=self.version_id:
            self.version_id=key;self.target_version_id=key;self.analysis_anchor_id=None;self.analysis_anchor_code=None
    def query(self,key):return self.filters.get(key,TableQuery())
    def navigate(self,page):
        if page not in dict(NAVIGATION):raise ValueError('Unknown navigation destination.')
        self.page=page
