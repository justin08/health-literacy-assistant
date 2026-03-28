"""
Helper functions for processing Figma data
"""

from typing import Dict, Any, List

def format_figma_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format and clean Figma data for display"""
    if not raw_data:
        return {}
    
    formatted = {
        'name': raw_data.get('name', 'Unknown'),
        'lastModified': raw_data.get('lastModified', ''),
        'version': raw_data.get('version', ''),
        'thumbnailUrl': raw_data.get('thumbnailUrl', ''),
        'document': raw_data.get('document', {}),
        'components': extract_components(raw_data),
        'statistics': calculate_statistics(raw_data)
    }
    
    return formatted

def extract_components(data: Dict[str, Any]) -> List[Dict]:
    """Extract components from Figma document"""
    components = []
    document = data.get('document', {})
    
    def traverse_node(node):
        if node.get('type') == 'COMPONENT':
            components.append({
                'id': node.get('id'),
                'name': node.get('name'),
                'type': node.get('type'),
                'visible': node.get('visible', True)
            })
        for child in node.get('children', []):
            traverse_node(child)
    
    if document:
        traverse_node(document)
    
    return components

def calculate_statistics(data: Dict[str, Any]) -> Dict[str, int]:
    """Calculate statistics from design data"""
    stats = {
        'total_frames': 0,
        'total_components': 0,
        'total_text_nodes': 0
    }
    
    document = data.get('document', {})
    
    def count_nodes(node):
        node_type = node.get('type', '')
        if node_type == 'FRAME':
            stats['total_frames'] += 1
        elif node_type == 'COMPONENT':
            stats['total_components'] += 1
        elif node_type == 'TEXT':
            stats['total_text_nodes'] += 1
        for child in node.get('children', []):
            count_nodes(child)
    
    if document:
        count_nodes(document)
    
    return stats
