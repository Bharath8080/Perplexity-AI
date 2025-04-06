import streamlit as st
import requests
import json
import os
import folium
from streamlit_folium import folium_static
from dotenv import load_dotenv

# Import Phidata components
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.duckduckgo import DuckDuckGo

# Load environment variables
load_dotenv()

# Configure API keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# Serper API endpoints
SHOPPING_SEARCH_URL = "https://google.serper.dev/shopping"
VIDEO_SEARCH_URL = "https://google.serper.dev/videos"
SEARCH_URL = "https://google.serper.dev/search"
IMAGE_SEARCH_URL = "https://google.serper.dev/images"
MAPS_SEARCH_URL = "https://google.serper.dev/maps"

# API headers
headers = {
    'X-API-KEY': SERPER_API_KEY,
    'Content-Type': 'application/json'
}

# Page configuration
st.set_page_config(
    page_title="Perplexity-like Assistant",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS to make the interface more compact and Perplexity-like
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stTextArea textarea {
        height: 60px;
    }
    .result-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .video-container {
        margin-bottom: 10px;
    }
    .product-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 8px;
        height: 100%;
    }
    .image-grid img {
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .stButton button {
        background-color: #6C5CE7;
        color: white;
        font-weight: bold;
    }
    .map-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .place-card {
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize agent
@st.cache_resource
def initialize_agent():
    return Agent(
        name="Perplexity Assistant",
        model=Gemini(id="gemini-2.0-flash-exp"),
        tools=[DuckDuckGo()],
        markdown=True,
    )

# Function to perform serper search
def serper_search(query, search_type="search"):
    url = SEARCH_URL
    if search_type == "shopping":
        url = SHOPPING_SEARCH_URL
    elif search_type == "videos":
        url = VIDEO_SEARCH_URL
    elif search_type == "images":
        url = IMAGE_SEARCH_URL
    elif search_type == "maps":
        url = MAPS_SEARCH_URL
    
    payload = json.dumps({"q": query})
    response = requests.post(url, headers=headers, data=payload)
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Main application
def main():
    st.title("🔍 Perplexity AI")
    
    # Initialize the agent
    assistant = initialize_agent()
    
    # Sidebar with content section toggles
    with st.sidebar:
        st.title("Content Sections")
        st.write("Select which content sections to display in results:")
        
        # Text results are shown by default and can't be disabled
        st.checkbox("📝 AI Answer", value=True, disabled=True, help="AI answer is always shown")
        
        # Optional content sections
        show_maps = st.checkbox("🗺️ Map Results", value=False)
        show_images = st.checkbox("🖼️ Image Results", value=False)
        show_videos = st.checkbox("📹 Related Videos", value=False)
        show_shopping = st.checkbox("🛒 Related Products", value=False)
    
    # Create search interface in main area
    query = st.text_area("Ask me anything:", height=68, placeholder="Ask any question to search for information, images, videos, products, and places...")
    
    search_button = st.button("🔍 Search", key="general_search", use_container_width=True)
    
    # Process query when search button is clicked
    if search_button and query:
        # Set up placeholder for progress
        progress_placeholder = st.empty()
        
        with progress_placeholder.container():
            st.info("🔍 Searching for information...")
        
        # Initialize containers for different result types
        text_container = st.container()
        
        # Only create containers for selected result types
        maps_container = st.container() if show_maps else None
        image_container = st.container() if show_images else None
        video_container = st.container() if show_videos else None
        shopping_container = st.container() if show_shopping else None
        
        # Always fetch general search results
        with st.spinner():
            # Fetch general search results for AI answer (always needed)
            search_results = serper_search(query)
            
            # Only fetch other results if their sections are enabled
            maps_results = serper_search(query, search_type="maps") if show_maps else None
            image_results = serper_search(query, search_type="images") if show_images else None
            video_results = serper_search(query, search_type="videos") if show_videos else None
            shopping_results = serper_search(query, search_type="shopping") if show_shopping else None
        
        # Clear progress once searches are complete
        progress_placeholder.empty()
        
        # Display AI Answer first (always shown)
        with text_container:
            st.markdown("### 📝 AI Answer")
            
            # Format search results for agent
            search_content = ""
            if search_results and "organic" in search_results:
                for result in search_results["organic"][:5]:
                    search_content += f"Title: {result.get('title', 'No title')}\n"
                    search_content += f"Link: {result.get('link', 'No link')}\n"
                    search_content += f"Snippet: {result.get('snippet', 'No snippet')}\n\n"
            
            # Pass search results to the agent for processing
            prompt = f"""
            Based on the following search results and your knowledge, provide a comprehensive answer to the query: "{query}"
            
            Search Results:
            {search_content}
            
            Provide a detailed, well-structured response that synthesizes information from the search results.
            Include relevant facts, examples, and explanations.
            """
            
            response = assistant.run(prompt)
            st.markdown(response.content)
            
            # Show sources
            if search_results and "organic" in search_results:
                with st.expander("📚 Sources"):
                    for i, result in enumerate(search_results["organic"][:5], 1):
                        st.markdown(f"**{i}. [{result.get('title', 'No title')}]({result.get('link', '#')})**")
                        st.markdown(f"_{result.get('snippet', 'No snippet')}_")
                        st.divider()
        
        # Display maps results only if selected
        if show_maps and maps_container:
            with maps_container:
                st.markdown("### 🗺️ Map Results")
                
                if maps_results and "places" in maps_results and len(maps_results["places"]) > 0:
                    # Get the first location's coordinates for map center
                    first_place = maps_results["places"][0]
                    map_center = [
                        first_place.get("latitude", 0), 
                        first_place.get("longitude", 0)
                    ]
                    
                    # Create two columns - one for map, one for place details
                    map_col, info_col = st.columns([3, 2])
                    
                    with map_col:
                        # Create map centered on the first result
                        m = folium.Map(location=map_center, zoom_start=14)
                        
                        # Add markers for all places
                        for place in maps_results["places"]:
                            lat = place.get("latitude")
                            lng = place.get("longitude")
                            title = place.get("title", "Unknown Location")
                            address = place.get("address", "No address available")
                            rating = place.get("rating", "N/A")
                            
                            if lat and lng:
                                popup_text = f"""
                                <b>{title}</b><br>
                                {address}<br>
                                Rating: {rating}
                                """
                                
                                folium.Marker(
                                    location=[lat, lng],
                                    popup=folium.Popup(popup_text, max_width=300),
                                    tooltip=title
                                ).add_to(m)
                        
                        # Display the map
                        folium_static(m, width=600)
                    
                    with info_col:
                        # Display place details
                        for place in maps_results["places"][:5]:  # Limit to 5 places
                            title = place.get("title", "Unknown Location")
                            address = place.get("address", "No address available")
                            rating = place.get("rating", "N/A")
                            rating_count = place.get("ratingCount", "0")
                            phone = place.get("phoneNumber", "Not available")
                            website = place.get("website", "#")
                            place_type = place.get("type", "Location")
                            
                            # Get opening hours
                            hours = place.get("openingHours", {})
                            hours_text = "<br>".join([f"{day}: {time}" for day, time in hours.items()]) if hours else "Hours not available"
                            
                            st.markdown(
                                f"""
                                <div class="place-card">
                                    <h3>{title}</h3>
                                    <p><b>📍 Address:</b> {address}</p>
                                    <p><b>⭐ Rating:</b> {rating} ({rating_count} reviews)</p>
                                    <p><b>📞 Phone:</b> {phone}</p>
                                    <p><b>🏢 Type:</b> {place_type}</p>
                                    <p><b>🕒 Hours:</b><br>{hours_text}</p>
                                    <p><a href="{website}" target="_blank">Visit Website</a></p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No map results available for this query.")
        
        # Display image results only if selected
        if show_images and image_container:
            with image_container:
                st.markdown("### 🖼️ Image Results")
                
                if image_results and "images" in image_results:
                    images = image_results["images"][:10]  # Display up to 10 images
                    
                    # Create a 5-column grid for images
                    image_cols = st.columns(5)
                    
                    for i, img in enumerate(images):
                        with image_cols[i % 5]:
                            # Display image with its title
                            st.image(
                                img.get("imageUrl", ""),
                                use_container_width=True,
                                caption=img.get("title", "").split("...")[0] if img.get("title") else ""
                            )
                else:
                    st.info("No image results available for this query.")
        
        # Display video results only if selected
        if show_videos and video_container:
            with video_container:
                st.markdown("### 📹 Related Videos")
                
                if video_results and "videos" in video_results:
                    # Filter for YouTube videos
                    youtube_videos = [
                        video for video in video_results["videos"]
                        if video.get("source", "").strip().lower() == "youtube"
                    ]
                    
                    if youtube_videos:
                        cols = st.columns(3)
                        for idx, video in enumerate(youtube_videos[:6]):
                            title = video.get("title", "Unknown Video")
                            link = video.get("link", "#")
                            duration = video.get("duration", "Unknown duration")
                            channel = video.get("channel", "Unknown Channel")
                            
                            # Extract YouTube video ID safely
                            if "youtube.com/watch?v=" in link:
                                video_id = link.split("v=")[-1].split("&")[0]
                                embed_url = f"https://www.youtube.com/embed/{video_id}"
                            else:
                                continue
                                
                            with cols[idx % 3]:
                                st.video(embed_url)
                                st.markdown(f"**{title}**\n\n📺 {channel} | ⏱️ {duration}")
                    else:
                        st.info("No relevant videos found for this query.")
                else:
                    st.info("No video results available.")
        
        # Display shopping results only if selected
        if show_shopping and shopping_container:
            with shopping_container:
                st.markdown("### 🛒 Related Products")
                
                if shopping_results and "shopping" in shopping_results:
                    products = shopping_results["shopping"]
                    
                    # Display products in a 5-column grid
                    cols = st.columns(5)
                    for idx, product in enumerate(products[:10]):
                        title = product.get("title", "Unknown Product")
                        link = product.get("link", "#")
                        price = product.get("price", "Price not available")
                        source = product.get("source", "Unknown Source")
                        image_url = product.get("imageUrl", "")
                        rating = product.get("rating", "No rating")
                        
                        with cols[idx % 5]:
                            st.markdown(
                                f"""
                                <div class="product-card">
                                    <img src="{image_url}" style="width:100%; height:100px; object-fit:contain;">
                                    <p style="font-size:12px; font-weight:bold; margin:5px 0; white-space:nowrap; 
                                    overflow:hidden; text-overflow:ellipsis;">
                                        <a href="{link}" target="_blank">{title}</a>
                                    </p>
                                    <p style="font-size:12px; margin:5px 0;">💲 <b>{price}</b></p>
                                    <p style="font-size:12px; margin:0;">⭐ {rating} | 🏬 {source}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No shopping results available for this query.")

if __name__ == "__main__":
    main()
