"""Legend features for graph visualization (integrated with NetworkX node_link_data)."""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
from enum import Enum
from collections import defaultdict
import html as html_escape
import re


# ----------------------------------------------------------------------
# ENUMS
# ----------------------------------------------------------------------

class LegendPosition(Enum):
    """Positions for legend placement."""
    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"
    LEFT = "left"
    RIGHT = "right"


# ----------------------------------------------------------------------
# NODE & EDGE ENTRY MODELS
# ----------------------------------------------------------------------

@dataclass
class NodeLegendEntry:
    """Configuration for a single node legend entry."""
    label: str
    color: str
    shape: Literal["circle", "square", "diamond", "triangle"] = "circle"
    size: int = 10
    border_color: Optional[str] = None
    border_width: int = 0

    def to_dict(self):
        return {
            "label": self.label,
            "color": self.color,
            "shape": self.shape,
            "size": self.size,
            "border_color": self.border_color,
            "border_width": self.border_width
        }


@dataclass
class EdgeLegendEntry:
    """Configuration for a single edge legend entry."""
    label: str
    color: str
    width: int = 2
    style: Literal["solid", "dashed", "dotted"] = "solid"
    arrow: bool = True

    def to_dict(self):
        return {
            "label": self.label,
            "color": self.color,
            "width": self.width,
            "style": self.style,
            "arrow": self.arrow
        }


# ----------------------------------------------------------------------
# LEGEND CONFIGURATION
# ----------------------------------------------------------------------

@dataclass
class LegendConfig:
    """Complete legend configuration."""
    enabled: bool = True
    position: LegendPosition = LegendPosition.TOP_RIGHT
    draggable: bool = True
    collapsible: bool = True
    background_color: str = "#ffffff"
    border_color: str = "#cccccc"
    opacity: float = 0.9

    node_entries: List[NodeLegendEntry] = field(default_factory=list)
    edge_entries: List[EdgeLegendEntry] = field(default_factory=list)

    def add_node_entry(self, label: str, color: str, **kwargs):
        entry = NodeLegendEntry(label=label, color=color, **kwargs)
        self.node_entries.append(entry)
        return entry

    def add_edge_entry(self, label: str, color: str, **kwargs):
        entry = EdgeLegendEntry(label=label, color=color, **kwargs)
        self.edge_entries.append(entry)
        return entry

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "position": self.position.value,
            "draggable": self.draggable,
            "collapsible": self.collapsible,
            "background_color": self.background_color,
            "border_color": self.border_color,
            "opacity": self.opacity,
            "node_entries": [e.to_dict() for e in self.node_entries],
            "edge_entries": [e.to_dict() for e in self.edge_entries]
        }


# ----------------------------------------------------------------------
# LEGEND BUILDER
# ----------------------------------------------------------------------

class LegendBuilder:
    """Automatically build legends from graph data."""
    
    # Constants for HTML generation
    NODE_SIZE_PADDING = 6
    EDGE_HEIGHT_PADDING = 6
    SVG_LINE_LENGTH = 50
    ITEM_MARGIN = 6
    MAX_EDGE_HEIGHT = 20
        
    @staticmethod
    def from_graph_data(graph_data: Dict[str, Any], auto_detect: bool = True) -> LegendConfig:
        legend = LegendConfig()

        if auto_detect:
            # Auto-detect node categories
            node_categories = LegendBuilder._detect_node_categories(graph_data)
            for category, props in node_categories.items():
                legend.add_node_entry(
                    label=category,
                    color=props.get('color', '#666666'),
                    shape=props.get('shape', 'circle'),
                    size=props.get('size', 10)
                )

            # Auto-detect edge categories
            edge_categories = LegendBuilder._detect_edge_categories(graph_data)
            for category, props in edge_categories.items():
                legend.add_edge_entry(
                    label=category,
                    color=props.get('color', '#999999'),
                    width=props.get('width', 2),
                    style=props.get('style', 'solid')
                )

        # Merge explicit legend data if present
        metadata = graph_data.get('metadata', {})
        if 'node_legend' in metadata:
            legend = LegendBuilder._merge_explicit_legend(legend, metadata['node_legend'], 'node')
        if 'edge_legend' in metadata:
            legend = LegendBuilder._merge_explicit_legend(legend, metadata['edge_legend'], 'edge')

        return legend

    # ------------------------------------------------------------------
    # INTERNAL DETECTION HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _merge_explicit_legend(legend: LegendConfig, explicit_data: Dict, legend_type: str) -> LegendConfig:
        if legend_type == 'node':
            for entry in explicit_data:
                legend.add_node_entry(
                    label=entry.get('label', ''),
                    color=entry.get('color', '#666666'),
                    shape=entry.get('shape', 'circle'),
                    size=entry.get('size', 10),
                    border_color=entry.get('border_color'),
                    border_width=entry.get('border_width', 0)
                )
        elif legend_type == 'edge':
            for entry in explicit_data:
                legend.add_edge_entry(
                    label=entry.get('label', ''),
                    color=entry.get('color', '#999999'),
                    width=entry.get('width', 2),
                    style=entry.get('style', 'solid'),
                    arrow=entry.get('arrow', True)
                )
        return legend

    @staticmethod
    def _detect_node_categories(graph_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Detect unique node categories and properties, even if no color is provided."""
        categories = defaultdict(lambda: {'colors': set(), 'shapes': set(), 'sizes': set()})
        nodes = graph_data.get('nodes', [])

        for node in nodes:
            metadata = node.get('metadata', node)
            category = metadata.get('legend_category', metadata.get('type', 'default'))

            # Always create the category
            categories[category]  # ensures it exists

            color = metadata.get('color')
            if color and color.strip():
                categories[category]['colors'].add(color)
            if 'shape' in metadata:
                categories[category]['shapes'].add(metadata['shape'])
            if 'size' in metadata:
                categories[category]['sizes'].add(metadata['size'])

        result = {}
        for cat, props in categories.items():
            result[cat] = {
                'color': list(props['colors'])[0] if props['colors'] else None,
                'shape': list(props['shapes'])[0] if props['shapes'] else 'circle',
                'size': int(sum(props['sizes']) / len(props['sizes'])) if props['sizes'] else 10
            }
        return result

    @staticmethod
    def _detect_edge_categories(graph_data: Dict[str, Any]) -> Dict[str, Dict]:
        """Detect unique edge categories and properties, even if no color is provided."""
        categories = defaultdict(lambda: {'colors': set(), 'widths': set(), 'styles': set()})
        edges = graph_data.get('edges', [])

        for edge in edges:
            metadata = edge.get('metadata', edge)
            category = metadata.get('legend_category', metadata.get('type', 'default'))

            # Always create the category
            categories[category]

            color = metadata.get('color')
            if color and color.strip():
                categories[category]['colors'].add(color)
            if 'weight' in metadata or 'width' in metadata:
                categories[category]['widths'].add(metadata.get('weight', metadata.get('width')))
            if 'style' in metadata:
                categories[category]['styles'].add(metadata['style'])

        result = {}
        for cat, props in categories.items():
            result[cat] = {
                'color': list(props['colors'])[0] if props['colors'] else None,
                'width': int(sum(props['widths']) / len(props['widths'])) if props['widths'] else 2,
                'style': list(props['styles'])[0] if props['styles'] else 'solid'
            }
        return result

    # ------------------------------------------------------------------
    # VALIDATION HELPERS
    # ------------------------------------------------------------------
    @staticmethod
    def _is_valid_color(color: str) -> bool:
        """Check if color is a valid CSS color value."""
        if not color or not isinstance(color, str) or not color.strip():
            return False
        color = color.strip()
        # Match hex colors, rgb/rgba, hsl/hsla, or named colors
        patterns = [
            r'^#[0-9a-fA-F]{3,8}$',  # Hex colors
            r'^rgba?\([^)]+\)$',      # RGB/RGBA
            r'^hsla?\([^)]+\)$',      # HSL/HSLA
            r'^[a-z]+$'               # Named colors (basic check)
        ]
        return any(re.match(pattern, color, re.IGNORECASE) for pattern in patterns)
    
    @staticmethod
    def _sanitize_dimension(value: Any, default: int = 10) -> int:
        """Ensure dimension values are positive integers."""
        try:
            val = int(value)
            return max(1, val)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _get_dash_pattern(style: str) -> str:
        """Get SVG stroke-dasharray pattern for edge style."""
        patterns = {
            "solid": "none",
            "dashed": "4,3",
            "dotted": "1,3"
        }
        return patterns.get(style.lower() if style else "", "none")
    
    @staticmethod
    def _get_shape_radius(shape: str) -> str:
        """Get CSS border-radius for node shape."""
        return "50%" if shape and shape.lower() == "circle" else "4px"

    # ------------------------------------------------------------------
    # HTML GENERATION
    # ------------------------------------------------------------------
    @staticmethod
    def build_html(graph_data: Dict[str, Any], dark_mode: bool = False) -> str:
        """
        Build a modern, theme-aware HTML legend from graph data.
        
        Args:
            graph_data: Dictionary containing graph configuration and data
            dark_mode: Whether to use dark theme colors
            
        Returns:
            HTML string for the legend with proper escaping and validation
        """
        legend = LegendBuilder.from_graph_data(graph_data)

        # === Palette ===
        if dark_mode:
            palette = dict(
                background="#1f1f25",
                text="#f0f0f5",
                border="#3a3a40",
                heading="#7ddba3",
                node_default="#7ddba3",
                edge_default="#b5b8c5",
            )
        else:
            palette = dict(
                background="#ffffff",
                text="#111111",
                border="#cccccc",
                heading="#222222",
                node_default="#000000",
                edge_default="#000000",
            )

        # === Container ===
        html_parts = [
            f'<div class="legend-container" role="figure" aria-label="Graph legend" style="'
            f'font-family: Inter, Arial, sans-serif; font-size: 14px; '
            f'color:{palette["text"]}; background:{palette["background"]}; '
            f'border:1px solid {palette["border"]}; border-radius:12px; '
            f'box-shadow:0 2px 8px rgba(0,0,0,0.15); padding:16px 20px; '
            f'width:fit-content; max-width:260px; opacity:{legend.opacity}; '
            f'backdrop-filter:blur(6px);">'
        ]

        html_parts.append(
            f'<h3 style="margin:0 0 12px 0; font-size:16px; color:{palette["heading"]}; '
            f'font-weight:600;">Legend</h3>'
        )

        # === Node section ===
        if legend.node_entries:
            html_parts.append('<div class="node-legend" style="margin-bottom:14px;">')
            html_parts.append(
                '<h4 style="margin:4px 0 6px 0; font-size:13px; font-weight:600;">Nodes</h4>'
            )
            html_parts.append('<ul style="list-style:none; padding:0; margin:0;">')

            for entry in legend.node_entries:
                # Validate and use default if missing/invalid
                color = (
                    entry.color 
                    if LegendBuilder._is_valid_color(entry.color) 
                    else palette["node_default"]
                )
                
                # Validate border color
                border_color = (
                    entry.border_color 
                    if LegendBuilder._is_valid_color(entry.border_color)
                    else palette["border"]
                )
                
                # Sanitize dimensions
                size = LegendBuilder._sanitize_dimension(
                    entry.size, 
                    default=10
                ) + LegendBuilder.NODE_SIZE_PADDING
                
                border_width = LegendBuilder._sanitize_dimension(
                    entry.border_width,
                    default=0
                )
                
                # Get shape styling
                shape_css = LegendBuilder._get_shape_radius(entry.shape)
                
                # Escape user-provided label
                safe_label = html_escape.escape(entry.label)

                html_parts.append(
                    f'<li style="display:flex; align-items:center; '
                    f'margin:{LegendBuilder.ITEM_MARGIN}px 0;">'
                    f'<span style="display:inline-block; width:{size}px; height:{size}px; '
                    f'border-radius:{shape_css}; background:{color}; '
                    f'border:{border_width}px solid {border_color}; '
                    f'margin-right:10px; flex-shrink:0;" '
                    f'aria-hidden="true"></span>'
                    f'<span>{safe_label}</span></li>'
                )
            html_parts.append('</ul></div>')

        # === Edge section ===
        if legend.edge_entries:
            html_parts.append('<div class="edge-legend">')
            html_parts.append(
                '<h4 style="margin:4px 0 6px 0; font-size:13px; font-weight:600;">Edges</h4>'
            )
            html_parts.append('<ul style="list-style:none; padding:0; margin:0;">')

            for entry in legend.edge_entries:
                # Validate color
                stroke_color = (
                    entry.color 
                    if LegendBuilder._is_valid_color(entry.color)
                    else palette["edge_default"]
                )
                
                # Sanitize width
                edge_width = LegendBuilder._sanitize_dimension(
                    entry.width,
                    default=2
                )
                
                # Get dash pattern
                dash_pattern = LegendBuilder._get_dash_pattern(entry.style)
                
                # Escape user-provided label
                safe_label = html_escape.escape(entry.label)

                html_parts.append(
                    f'<li style="display:flex; align-items:center; '
                    f'margin:{LegendBuilder.ITEM_MARGIN}px 0;">'
                    f'<svg width="{LegendBuilder.SVG_LINE_LENGTH}" height="{edge_width * 2}" '
                    f'viewBox="0 0 {LegendBuilder.SVG_LINE_LENGTH} {edge_width * 2}" '
                    f'style="margin-right:10px; display:block; flex-shrink:0;" '
                    f'aria-hidden="true">'
                    f'<line x1="0" y1="{edge_width}" '
                    f'x2="{LegendBuilder.SVG_LINE_LENGTH}" y2="{edge_width}" '
                    f'stroke="{stroke_color}" stroke-width="{edge_width/10}" '
                    f'stroke-dasharray="{dash_pattern}" stroke-linecap="round" />'
                    f'</svg>'
                    f'<span>{safe_label}</span></li>'
                )
            html_parts.append('</ul></div>')

        html_parts.append('</div>')
        return "\n".join(html_parts)