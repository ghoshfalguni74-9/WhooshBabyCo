from pathlib import Path


def test_heading_uses_algerian_font():
    """Ensure the sample HTML contains a heading with Algerian-style font."""
    project_root = Path(__file__).resolve().parents[1]
    html_path = project_root / "whoosh_babyco.html"
    assert html_path.exists(), f"Expected sample HTML at {html_path}"

    content = html_path.read_text(encoding="utf-8")
    lower = content.lower()

    assert "<h1" in lower, "No <h1> tag found in sample HTML"
    assert "whoosh" in lower, "Heading does not contain the company name 'whoosh'"
    # Check for font-family declaration mentioning Algerian (case-insensitive)
    assert "font-family" in lower, "No font-family declaration found in sample HTML"
    assert "algerian" in lower, "Expected 'Algerian' font-family in sample HTML"


def test_homepage_keeps_cart_navigation_without_featured_cart_controls():
    """Ensure the homepage cart link remains while featured cards stay informational."""
    project_root = Path(__file__).resolve().parents[1]
    html_path = project_root / "whoosh_babyco.html"
    content = html_path.read_text(encoding="utf-8")
    lower = content.lower()

    assert 'href="cart.html"' in lower, "Homepage cart link is missing"
    assert "baby care kit" not in lower, "Baby Care Kit should not appear on the homepage"
    assert "add-to-cart" not in lower, "Featured products should not show add-to-cart controls"


def test_cart_page_renders_persisted_cart_items():
    """Ensure the cart link points to a page that reads and manages saved items."""
    project_root = Path(__file__).resolve().parents[1]
    homepage = (project_root / "whoosh_babyco.html").read_text(encoding="utf-8").lower()
    cart = (project_root / "cart.html").read_text(encoding="utf-8").lower()

    assert 'href="cart.html"' in homepage, "Homepage cart icon does not open the cart page"
    assert "whoosh_cart" in cart, "Cart page does not read persisted cart items"
    assert "clear cart" in cart, "Cart page missing clear-cart control"
    assert "data-action=\"increase\"" in cart, "Cart page missing quantity controls"


def test_logged_in_profile_can_open_edit_mode():
    """Ensure the user icon leads to details and the edit form uses the update API."""
    project_root = Path(__file__).resolve().parents[1]
    homepage = (project_root / "whoosh_babyco.html").read_text(encoding="utf-8").lower()
    profile = (project_root / "profile.html").read_text(encoding="utf-8").lower()
    login_script = (project_root / "admin" / "login.js").read_text(encoding="utf-8").lower()
    server = (project_root / "admin" / "server.py").read_text(encoding="utf-8").lower()

    assert 'href="profile.html"' in homepage, "Person icon should open the profile page"
    assert "api/user-details" in profile, "Profile page should load saved user details"
    assert "edit=1" in profile, "Profile page should expose edit mode"
    assert "api/update-user" in login_script, "Edit mode should save through the update endpoint"
    assert "/api/update-user" in server, "Backend update endpoint is missing"


def test_category_storefront_covers_all_shopping_categories():
    """Ensure every homepage category opens the reusable product storefront."""
    project_root = Path(__file__).resolve().parents[1]
    homepage = (project_root / "whoosh_babyco.html").read_text(encoding="utf-8").lower()
    category = (project_root / "category.html").read_text(encoding="utf-8").lower()

    for key in ("soap", "shampoo", "oil", "clothes", "toys", "accessories"):
        assert key in homepage, f"Homepage missing {key} category routing"
        assert f"{key}:" in category, f"Storefront missing {key} product catalog"
    assert "add to cart" in category, "Category storefront missing product purchase controls"
    assert "whoosh_logged_in_user" in category, "Category cart actions are not login-gated"


def test_saved_soap_catalog_entries_are_present():
    """Protect the current soap product names, descriptions, and prices."""
    project_root = Path(__file__).resolve().parents[1]
    category = (project_root / "category.html").read_text(encoding="utf-8").lower()

    assert "johnson's baby soap" in category
    assert "milk protien , turmeric & shea butter." in category
    assert "himalaya nourishing baby soap" in category
    assert "tedibar" in category
    assert "65" in category and "84" in category and "177" in category


def test_product_cards_show_increased_price_and_discount():
    """Ensure product cards show the requested 8% increase and 5% discount."""
    project_root = Path(__file__).resolve().parents[1]
    category = (project_root / "category.html").read_text(encoding="utf-8").lower()

    assert "baseprice * 1.08" in category
    assert "5% off" in category
    assert "prices.saleprice" in category
    assert "onerror" in category, "Product images should have a fallback source"


def test_soap_picture_addresses_are_saved_as_direct_images():
    """Ensure saved soap picture addresses are usable by product image elements."""
    project_root = Path(__file__).resolve().parents[1]
    category = (project_root / "category.html").read_text(encoding="utf-8").lower()

    assert "encrypted-tbn0.gstatic.com/images?q=tbn:and9gcqxcf4va0isoo" in category
    assert "clickoncare.com/cdn/shop/files/4_3b591577-9065-4590-b330-735fabd69be9.jpg" in category
    assert "m.media-amazon.com/images/i/51ebqy h9oc l.jpg".replace(" ", "") in category
    assert "m.media-amazon.com/images/i/51bfpswdupl.jpg" in category
    assert "share.google" not in category


def test_otp_ui_handles_unconfigured_email_service():
    """Ensure the signup UI displays the local fallback OTP when SMTP is unavailable."""
    project_root = Path(__file__).resolve().parents[1]
    login_script = (project_root / "admin" / "login.js").read_text(encoding="utf-8").lower()
    server = (project_root / "admin" / "server.py").read_text(encoding="utf-8").lower()

    assert "developmentotp" in login_script
    assert "developmentotp" in server
    assert "store_email_otp(email, otp)" in server
