# backend/tools/citation.py
from typing import Dict
from langchain.tools import tool

class CitationGeneratorTool:
    def __init__(self):
        """Initialize the Citation Generator Tool."""
        pass
        
    def _format_apa(self, source_info: Dict) -> str:
        """Format citation in APA style."""
        authors = source_info.get("authors", "")
        if isinstance(authors, list):
            authors = ", ".join(authors)
        
        year = source_info.get("year", "")
        if not year and "date" in source_info:
            try:
                from datetime import datetime
                year = datetime.strptime(source_info["date"], "%Y-%m-%d").year
            except:
                year = source_info.get("date", "")
        
        title = source_info.get("title", "")
        url = source_info.get("url", "")
        publisher = source_info.get("publisher", "")
        
        if source_info.get("type") == "webpage":
            return f"{authors} ({year}). {title}. {publisher}. Retrieved from {url}"
        elif source_info.get("type") == "article":
            journal = source_info.get("journal", "")
            volume = source_info.get("volume", "")
            pages = source_info.get("pages", "")
            return f"{authors} ({year}). {title}. {journal}, {volume}, {pages}. {url}"
        elif source_info.get("type") == "book":
            return f"{authors} ({year}). {title}. {publisher}."
        else:
            return f"{authors} ({year}). {title}. {url}"
    
    def _format_mla(self, source_info: Dict) -> str:
        """Format citation in MLA style."""
        authors = source_info.get("authors", "")
        if isinstance(authors, list):
            authors = ", ".join(authors)
        
        title = source_info.get("title", "")
        url = source_info.get("url", "")
        publisher = source_info.get("publisher", "")
        date = source_info.get("date", "")
        
        if source_info.get("type") == "webpage":
            return f"{authors}. \"{title}.\" {publisher}, {date}, {url}."
        elif source_info.get("type") == "article":
            journal = source_info.get("journal", "")
            volume = source_info.get("volume", "")
            pages = source_info.get("pages", "")
            return f"{authors}. \"{title}.\" {journal}, vol. {volume}, {date}, pp. {pages}, {url}."
        elif source_info.get("type") == "book":
            return f"{authors}. {title}. {publisher}, {date}."
        else:
            return f"{authors}. \"{title}.\" {date}, {url}."
    
    def generate_citation(self, source_info: Dict, style: str = "APA") -> str:
        """
        Generates a properly formatted citation based on source information.
        
        Args:
            source_info: Dictionary containing source metadata
            style: Citation style ("APA", "MLA", "Chicago", "Harvard")
            
        Returns:
            A formatted citation string
        """
        style = style.upper()
        
        try:
            if style == "APA":
                return self._format_apa(source_info)
            elif style == "MLA":
                return self._format_mla(source_info)
            elif style == "CHICAGO":
                # Implementation for Chicago style
                return f"Chicago style citation for {source_info.get('title', '')}"
            elif style == "HARVARD":
                # Implementation for Harvard style
                return f"Harvard style citation for {source_info.get('title', '')}"
            else:
                return f"Unsupported citation style: {style}"
        except Exception as e:
            return f"Citation generation failed: {str(e)}"