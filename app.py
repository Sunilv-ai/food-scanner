prompt = """
    Analyze the image provided.
    
    STEP 1: CHECK FOR INGREDIENTS
    Does this image contain a list of ingredients (e.g., "Ingredients: Milk, Sugar...")? 
    Note: A "Nutrition" table (Energy, Fat, Salt) is NOT an ingredients list.
    
    IF NO INGREDIENTS LIST IS VISIBLE:
    Return exactly this JSON:
    {
        "error": "missing_ingredients",
        "message": "I see Nutrition Facts, but not the Ingredient List. Please rotate the package and try again."
    }

    IF INGREDIENTS ARE FOUND:
    1. Identify the First 3 ingredients listed (Top by Mass).
    2. Classify EVERY ingredient into 'Simple_Processed' or 'Ultra_Processed'.
    3. Count total ingredients and calculate percentages.
    
    Return STRICT JSON:
    {
        "top_3_by_mass": ["item1", "item2", "item3"],
        "stats": {
            "total_count": 0,
            "simple_pct": 0,
            "ultra_processed_pct": 0
        },
        "lists": {
            "simple": ["item", "item"],
            "ultra": ["item", "item"]
        },
        "verdict": "One sentence summary."
    }
    """
