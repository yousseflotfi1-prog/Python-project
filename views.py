from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q

from .models import Book, Category, Order, OrderItem
from .forms import CustomUserCreationForm


# ---------------------------
# Helpers panier (session)
# ---------------------------
def _get_cart(request):
    cart = request.session.get("cart", {})
    if not isinstance(cart, dict):
        cart = {}
    return cart


def _cart_count(cart: dict) -> int:
    return sum(int(item.get("qty", 0)) for item in cart.values())


def _cart_items_and_total(cart: dict):
    items = []
    subtotal = 0

    for book_id, data in cart.items():
        try:
            qty = int(data.get("qty", 0))
        except Exception:
            qty = 0

        if qty <= 0:
            continue

        book = Book.objects.filter(id=book_id).first()
        if not book:
            continue

        line_total = book.prix * qty
        subtotal += line_total
        items.append({"book": book, "qty": qty, "line_total": line_total})

    return items, subtotal


# ---------------------------
# Accueil (books + filtre + recherche)
# ---------------------------
def accueil(request):
    query = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "all")

    books = Book.objects.all()
    categories = Category.objects.all()

    if cat and cat != "all":
        books = books.filter(category__id=cat)

    if query:
        books = books.filter(Q(titre__icontains=query) | Q(description__icontains=query))

    books = books.order_by("prix")

    cart = _get_cart(request)
    cart_count = _cart_count(cart)

    return render(request, "blog/accueil.html", {
        "books": books,
        "query": query,
        "categories": categories,
        "cat": cat,
        "cart_count": cart_count,
    })


# ---------------------------
# Panier
# ---------------------------
def cart_detail(request):
    cart = _get_cart(request)
    items, subtotal = _cart_items_and_total(cart)
    cart_count = _cart_count(cart)

    return render(request, "blog/cart.html", {
        "items": items,
        "subtotal": subtotal,
        "cart_count": cart_count,
    })


def cart_add(request, book_id):
    cart = _get_cart(request)
    key = str(book_id)
    cart.setdefault(key, {"qty": 0})
    cart[key]["qty"] = int(cart[key].get("qty", 0)) + 1
    request.session["cart"] = cart
    request.session.modified = True
    return redirect("cart_detail")


def cart_decrease(request, book_id):
    cart = _get_cart(request)
    key = str(book_id)
    if key in cart:
        cart[key]["qty"] = int(cart[key].get("qty", 0)) - 1
        if cart[key]["qty"] <= 0:
            cart.pop(key, None)
    request.session["cart"] = cart
    request.session.modified = True
    return redirect("cart_detail")


def cart_remove(request, book_id):
    cart = _get_cart(request)
    cart.pop(str(book_id), None)
    request.session["cart"] = cart
    request.session.modified = True
    return redirect("cart_detail")


# ---------------------------
# Checkout
# ---------------------------
def checkout(request):
    cart = _get_cart(request)
    items, subtotal = _cart_items_and_total(cart)
    cart_count = _cart_count(cart)

    if not items:
        return redirect("accueil")

    shipping_fee = 0
    total = subtotal + shipping_fee

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        city = request.POST.get("city", "").strip()
        payment_method = request.POST.get("payment_method", "COD")

        if payment_method not in ("COD", "CARD"):
            payment_method = "COD"

        if not full_name or not phone or not address:
            return render(request, "blog/checkout.html", {
                "items": items,
                "subtotal": subtotal,
                "shipping_fee": shipping_fee,
                "total": total,
                "cart_count": cart_count,
                "error": "Veuillez remplir: nom, téléphone, adresse.",
                "form": {
                    "full_name": full_name,
                    "phone": phone,
                    "address": address,
                    "city": city,
                    "payment_method": payment_method,
                }
            })

        order = Order.objects.create(
            full_name=full_name,
            phone=phone,
            address=address,
            city=city,
            payment_method=payment_method,
            shipping_fee=shipping_fee,
            total=total,
        )

        for it in items:
            OrderItem.objects.create(
                order=order,
                book=it["book"],
                price=it["book"].prix,
                quantity=it["qty"],
            )

        request.session["cart"] = {}
        request.session.modified = True

        return redirect("order_success", order_id=order.id)

    return render(request, "blog/checkout.html", {
        "items": items,
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "total": total,
        "cart_count": cart_count,
        "form": {"payment_method": "COD"},
    })


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "blog/order_success.html", {"order": order})


# ---------------------------
# Auth: Signup / Activate / Login / Logout
# ---------------------------
def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            activation_link = request.build_absolute_uri(f"/activate/{uid}/{token}/")

            user.email_user(
                subject="Activez votre compte",
                message=f"Bonjour {user.username}, cliquez ici : {activation_link}"
            )
            return render(request, "blog/signup_success.html", {"email": user.email})
    else:
        form = CustomUserCreationForm()

    return render(request, "blog/signup.html", {"form": form})


def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, "blog/activation_success.html")
    return render(request, "blog/activation_invalid.html")


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect("accueil")
    else:
        form = AuthenticationForm()
    return render(request, "blog/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("accueil")

