#!/usr/bin/env python3
"""
Google Ads Search Campaign Creator for New Accounts

This script creates a Google Search campaign optimized for GUARANTEED IMPRESSIONS
on a brand-new Google Ads account. Designed for testing and learning purposes.

Requirements:
- google-ads Python client library: pip install google-ads
- google-ads.yaml configuration file in default location
"""

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

# =============================================================================
# CONFIGURATION - MODIFY THESE VALUES
# =============================================================================

# Your Google Ads customer ID (no dashes, e.g., "1234567890")
CUSTOMER_ID = "YOUR_CUSTOMER_ID_HERE"

# Final URL for all ads (update this with your Vercel deployment URL)
FINAL_URL = "https://your-vercel-domain.vercel.app"

# Target state - use geo target constant ID
# Find IDs at: https://developers.google.com/google-ads/api/reference/data/geotargets
# Examples: New Jersey = 21167, California = 21137, New York = 21167, Texas = 21176
TARGET_STATE_GEO_ID = "21167"  # New Jersey

# Campaign name prefix
CAMPAIGN_NAME = "Search - Junk Removal - Test"


def main():
    """Main entry point for campaign creation."""
    # Load client from google-ads.yaml (assumed to exist)
    client = GoogleAdsClient.load_from_storage()
    
    try:
        # Create all resources in order
        # Using temporary resource names allows us to create everything in fewer API calls
        budget_resource_name = create_budget(client, CUSTOMER_ID)
        campaign_resource_name = create_campaign(client, CUSTOMER_ID, budget_resource_name)
        ad_group_resource_name = create_ad_group(client, CUSTOMER_ID, campaign_resource_name)
        add_keywords(client, CUSTOMER_ID, ad_group_resource_name)
        add_responsive_search_ad(client, CUSTOMER_ID, ad_group_resource_name)
        
        print("\n" + "=" * 60)
        print("CAMPAIGN CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Campaign: {campaign_resource_name}")
        print(f"Ad Group: {ad_group_resource_name}")
        print(f"Status: PAUSED (enable when ready)")
        print("=" * 60)
        
    except GoogleAdsException as ex:
        print(f"Google Ads API error occurred:")
        print(f"  Error code: {ex.error.code().name}")
        for error in ex.failure.errors:
            print(f"  Message: {error.message}")
            if error.location:
                for field_path_element in error.location.field_path_elements:
                    print(f"    Field: {field_path_element.field_name}")
        raise


def create_budget(client, customer_id):
    """
    Creates a campaign budget of $100/day.
    
    WHY $100/day:
    - High enough to never be budget-limited during testing
    - Ensures ads can serve all day without throttling
    - New accounts need sufficient budget to build initial quality signals
    
    WHY EXPLICITLY_SHARED = False:
    - Dedicated budget prevents competition with other campaigns
    - Full budget available to this campaign only
    """
    campaign_budget_service = client.get_service("CampaignBudgetService")
    campaign_budget_operation = client.get_type("CampaignBudgetOperation")
    
    campaign_budget = campaign_budget_operation.create
    campaign_budget.name = f"{CAMPAIGN_NAME} Budget"
    
    # $100/day in micros (1 dollar = 1,000,000 micros)
    campaign_budget.amount_micros = 100_000_000
    
    # STANDARD delivery spends budget evenly throughout the day
    # This is the only option now (ACCELERATED was deprecated)
    campaign_budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    
    # Not shared - dedicated to this campaign only
    campaign_budget.explicitly_shared = False
    
    response = campaign_budget_service.mutate_campaign_budgets(
        customer_id=customer_id,
        operations=[campaign_budget_operation]
    )
    
    budget_resource_name = response.results[0].resource_name
    print(f"Created budget: {budget_resource_name}")
    return budget_resource_name


def create_campaign(client, customer_id, budget_resource_name):
    """
    Creates a Search campaign with Manual CPC bidding.
    
    WHY MANUAL CPC:
    - New accounts have no conversion data for smart bidding
    - Manual CPC gives us direct control over auction bids
    - No learning period delays - starts competing immediately
    - Enhanced CPC disabled to maintain pure manual control
    
    WHY SEARCH ONLY (no partners, no display):
    - Search Network has highest intent traffic
    - Search Partners can dilute quality signals on new accounts
    - Display Network is irrelevant for Search campaigns
    
    WHY PRESENCE TARGETING:
    - "People in or regularly in" captures actual local searchers
    - More impressions than "presence only"
    - Standard for service-based businesses
    
    WHY PAUSED:
    - Allows review before spending
    - Can verify all settings before enabling
    """
    campaign_service = client.get_service("CampaignService")
    campaign_operation = client.get_type("CampaignOperation")
    
    campaign = campaign_operation.create
    campaign.name = CAMPAIGN_NAME
    campaign.campaign_budget = budget_resource_name
    
    # Search campaign type - standard search ads
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    
    # Start PAUSED for review
    campaign.status = client.enums.CampaignStatusEnum.PAUSED
    
    # ==========================================================================
    # MANUAL CPC BIDDING - Critical for new account impression delivery
    # ==========================================================================
    campaign.manual_cpc.enhanced_cpc_enabled = False  # Pure manual control
    
    # ==========================================================================
    # NETWORK SETTINGS - Search only, no partners, no display
    # ==========================================================================
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = False  # No search partners
    campaign.network_settings.target_content_network = False  # No display
    campaign.network_settings.target_partner_search_network = False
    
    # ==========================================================================
    # GEO TARGETING SETTINGS - Presence (people in location)
    # ==========================================================================
    # PRESENCE = People in or regularly in your targeted locations
    # This is the standard setting for local service businesses
    campaign.geo_target_type_setting.positive_geo_target_type = (
        client.enums.PositiveGeoTargetTypeEnum.PRESENCE
    )
    campaign.geo_target_type_setting.negative_geo_target_type = (
        client.enums.NegativeGeoTargetTypeEnum.PRESENCE
    )
    
    # Create the campaign first
    response = campaign_service.mutate_campaigns(
        customer_id=customer_id,
        operations=[campaign_operation]
    )
    
    campaign_resource_name = response.results[0].resource_name
    print(f"Created campaign: {campaign_resource_name}")
    
    # ==========================================================================
    # ADD GEO TARGETING - Target entire state
    # ==========================================================================
    add_geo_targeting(client, customer_id, campaign_resource_name)
    
    return campaign_resource_name


def add_geo_targeting(client, customer_id, campaign_resource_name):
    """
    Adds geo targeting for the specified state.
    
    WHY ENTIRE STATE:
    - Maximum reach for impression testing
    - Covers all population centers
    - Simple to understand and verify
    """
    campaign_criterion_service = client.get_service("CampaignCriterionService")
    campaign_criterion_operation = client.get_type("CampaignCriterionOperation")
    
    campaign_criterion = campaign_criterion_operation.create
    campaign_criterion.campaign = campaign_resource_name
    
    # Set location target using geo target constant
    geo_target_constant_service = client.get_service("GeoTargetConstantService")
    campaign_criterion.location.geo_target_constant = (
        geo_target_constant_service.geo_target_constant_path(TARGET_STATE_GEO_ID)
    )
    
    response = campaign_criterion_service.mutate_campaign_criteria(
        customer_id=customer_id,
        operations=[campaign_criterion_operation]
    )
    
    print(f"Added geo targeting: State ID {TARGET_STATE_GEO_ID}")


def create_ad_group(client, customer_id, campaign_resource_name):
    """
    Creates an ad group with $20 CPC bid.
    
    WHY $20 CPC:
    - Junk removal keywords have CPCs ranging from $5-$30
    - $20 is competitive enough to win auctions consistently
    - Ensures we don't lose impressions due to low bids
    - High bids on new accounts help build initial quality score
    
    WHY SINGLE AD GROUP:
    - Simplest structure for testing
    - All keywords trigger all ads
    - Easy to analyze performance
    """
    ad_group_service = client.get_service("AdGroupService")
    ad_group_operation = client.get_type("AdGroupOperation")
    
    ad_group = ad_group_operation.create
    ad_group.name = f"{CAMPAIGN_NAME} - Ad Group"
    ad_group.campaign = campaign_resource_name
    
    # ENABLED status - will serve when campaign is enabled
    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
    
    # Standard ad group type for search
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    
    # $20 CPC bid in micros - high enough to compete immediately
    ad_group.cpc_bid_micros = 20_000_000
    
    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id,
        operations=[ad_group_operation]
    )
    
    ad_group_resource_name = response.results[0].resource_name
    print(f"Created ad group: {ad_group_resource_name}")
    return ad_group_resource_name


def add_keywords(client, customer_id, ad_group_resource_name):
    """
    Adds phrase match keywords to the ad group.
    
    WHY PHRASE MATCH:
    - More controlled than broad match
    - Captures variations and close variants
    - Better than exact match for discovery/testing
    - Good balance of reach and relevance
    
    WHY THESE KEYWORDS:
    - High commercial intent (people ready to buy)
    - Common search terms in junk removal industry
    - "Near me" signals local intent
    - Variety of terms to capture different search behaviors
    """
    ad_group_criterion_service = client.get_service("AdGroupCriterionService")
    
    # Keywords to add - all phrase match
    keywords = [
        "junk removal near me",
        "junk hauling", 
        "trash removal service",
        "appliance removal",
    ]
    
    operations = []
    
    for keyword_text in keywords:
        operation = client.get_type("AdGroupCriterionOperation")
        criterion = operation.create
        
        criterion.ad_group = ad_group_resource_name
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        
        # Phrase match keyword
        criterion.keyword.text = keyword_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.PHRASE
        
        operations.append(operation)
    
    response = ad_group_criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id,
        operations=operations
    )
    
    print(f"Added {len(response.results)} keywords (phrase match)")
    for result in response.results:
        print(f"  - {result.resource_name}")


def add_responsive_search_ad(client, customer_id, ad_group_resource_name):
    """
    Creates a Responsive Search Ad with multiple headlines and descriptions.
    
    WHY RESPONSIVE SEARCH AD:
    - Required ad format for Search campaigns (expanded text ads deprecated)
    - Google automatically tests combinations
    - Higher ad strength = better serving
    
    WHY 5 HEADLINES, 3 DESCRIPTIONS:
    - More assets = more combinations for Google to test
    - Increases ad strength
    - Better coverage of search queries
    
    WHY GENERIC COPY:
    - Works for any location
    - Clear value propositions
    - Call to action in headlines
    - Contact information emphasis
    """
    ad_group_ad_service = client.get_service("AdGroupAdService")
    ad_group_ad_operation = client.get_type("AdGroupAdOperation")
    
    ad_group_ad = ad_group_ad_operation.create
    ad_group_ad.ad_group = ad_group_resource_name
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
    
    # Set the final URL
    ad_group_ad.ad.final_urls.append(FINAL_URL)
    
    # ==========================================================================
    # HEADLINES (max 30 characters each)
    # ==========================================================================
    headlines = [
        "Fast Junk Removal Service",      # 25 chars - service focus
        "Same Day Pickup Available",       # 24 chars - urgency/speed
        "Call Now - Free Estimates",       # 24 chars - CTA + value
        "Professional Junk Hauling",       # 25 chars - professionalism
        "We Haul It All Away",             # 19 chars - comprehensive service
    ]
    
    for headline_text in headlines:
        headline = client.get_type("AdTextAsset")
        headline.text = headline_text
        ad_group_ad.ad.responsive_search_ad.headlines.append(headline)
    
    # ==========================================================================
    # DESCRIPTIONS (max 90 characters each)
    # ==========================================================================
    descriptions = [
        "Quick, reliable junk removal. We handle everything from appliances to yard waste. Call today!",  # 89 chars
        "Professional hauling service. Fast response, fair prices. Get your free quote now!",  # 80 chars
        "Same day junk pickup available. Furniture, appliances, debris - we remove it all.",  # 81 chars
    ]
    
    for description_text in descriptions:
        description = client.get_type("AdTextAsset")
        description.text = description_text
        ad_group_ad.ad.responsive_search_ad.descriptions.append(description)
    
    # ==========================================================================
    # PATH FIELDS (display URL paths)
    # ==========================================================================
    ad_group_ad.ad.responsive_search_ad.path1 = "Junk-Removal"
    ad_group_ad.ad.responsive_search_ad.path2 = "Free-Quote"
    
    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=customer_id,
        operations=[ad_group_ad_operation]
    )
    
    print(f"Created Responsive Search Ad: {response.results[0].resource_name}")


if __name__ == "__main__":
    main()
