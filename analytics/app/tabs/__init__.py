"""
Analytics dashboard tab modules.
Each tab is implemented as a class that handles its own layout and callbacks.
"""

from .usage_statistics import UsageStatisticsTab
from .geographic_distribution import GeographicDistributionTab
from .generation_details import GenerationDetailsTab
from .image_upload_analysis import ImageUploadAnalysisTab

__all__ = [
    'UsageStatisticsTab',
    'GeographicDistributionTab',
    'GenerationDetailsTab',
    'ImageUploadAnalysisTab'
]
