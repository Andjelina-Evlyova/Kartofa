const tabs = document.querySelectorAll(".tab");
const cards = document.querySelectorAll(".menu-card");
const count = document.querySelector(".cart-count");
const cartDrawer = document.querySelector(".cart-drawer");
const cartOverlay = document.querySelector(".cart-overlay");
const cartItems = document.querySelector(".cart-items");
const cartTotal = document.querySelector(".cart-total strong");
const checkoutButton = document.querySelector(".checkout-button");
let cart = [];


const menuToggle = document.querySelector(".menu-toggle");
const nav = document.querySelector(".nav");
if (menuToggle && nav) {
    menuToggle.addEventListener("click", () => {
        const isOpen = nav.classList.toggle("open");
        menuToggle.setAttribute("aria-expanded", String(isOpen));
    });
    nav.querySelectorAll("a").forEach((link) => {
        link.addEventListener("click", () => {
            nav.classList.remove("open");
            menuToggle.setAttribute("aria-expanded", "false");
        });
    });
}

document.querySelectorAll(".menu-card").forEach((card) => {
    const price = card.querySelector(".card-bottom strong");
    const image = card.querySelector(".card-image");
    if (!price || !image) return;
    const badge = document.createElement("span");
    badge.className = "card-price";
    badge.textContent = price.textContent.trim();
    image.appendChild(badge);
});

function updateEstimatedReadyTime(itemCount) {
    const status = document.querySelector(".pickup-status strong");
    if (!status || itemCount === 0) return;
    status.textContent = `${itemCount} продукта — служителят ще зададе точен срок според натоварването на кухнята.`;
}

function openCart() {
    cartDrawer.classList.add("open");
    cartOverlay.classList.add("open");
    cartDrawer.setAttribute("aria-hidden", "false");
    cartOverlay.setAttribute("aria-hidden", "false");
}

function closeCart() {
    cartDrawer.classList.remove("open");
    cartOverlay.classList.remove("open");
    cartDrawer.setAttribute("aria-hidden", "true");
    cartOverlay.setAttribute("aria-hidden", "true");
}

function renderCart() {
    const itemCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    count.textContent = itemCount;
    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    cartTotal.textContent = `${total.toFixed(2)} €`;
    checkoutButton.disabled = cart.length === 0;
    updateEstimatedReadyTime(itemCount);

    if (!cart.length) {
        cartItems.innerHTML = '<p class="cart-empty">Количката е празна.</p>';
        return;
    }

    cartItems.innerHTML = cart.map((item, index) => `
        <div class="cart-item">
            <div><strong>${item.name}</strong><span>${item.price > 0 ? item.price.toFixed(2) + " €" : "По меню"}</span></div>
            <div class="quantity-controls">
                <button type="button" data-action="minus" data-index="${index}" aria-label="Премахни едно">−</button>
                <span>${item.quantity}</span>
                <button type="button" data-action="plus" data-index="${index}" aria-label="Добави едно">+</button>
            </div>
        </div>
    `).join("");
}

tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        tabs.forEach((item) => item.classList.remove("active"));
        tab.classList.add("active");
        const category = tab.dataset.category;
        cards.forEach((card) => {
            card.classList.toggle("hidden", category !== "all" && card.dataset.category !== category);
        });
    });
});

document.querySelectorAll(".add-button").forEach((button) => {
    button.addEventListener("click", () => {
        const name = button.dataset.name;
        const price = Number(button.dataset.price);
        if (price === 0) {
            alert("Цената и наличните варианти ще бъдат потвърдени от КартофЪ при поръчката.");
            return;
        }
        const existing = cart.find((item) => item.name === name);
        if (existing) existing.quantity += 1;
        else cart.push({ name, price, quantity: 1 });
        renderCart();
        button.textContent = "✓";
        button.classList.add("added");
        setTimeout(() => {
            button.textContent = "+";
            button.classList.remove("added");
        }, 900);
    });
});

function getBuilderSelection() {
    const size = document.querySelector('input[name="size"]:checked');
    const base = document.querySelector('input[name="base"]:checked');
    const toppings = [...document.querySelectorAll(".topping-options input:checked")];
    let price = Number(size.dataset.price) + Number(base.dataset.price);
    toppings.forEach((topping) => price += Number(topping.dataset.price));

    const names = toppings.map((topping) => topping.value);
    return {
        name: `КартофЪ по избор — ${size.value}`,
        description: `${base.value}${names.length ? `; ${names.join(", ")}` : ""}`,
        price,
    };
}

function updateBuilder() {
    const limit = Number(document.querySelector('input[name="size"]:checked').dataset.count);
    const toppings = [...document.querySelectorAll(".topping-options input")];
    let checkedCount = toppings.filter((item) => item.checked).length;
    while (checkedCount > limit) {
        const lastChecked = [...toppings].reverse().find((item) => item.checked);
        if (!lastChecked) break;
        lastChecked.checked = false;
        checkedCount -= 1;
    }
    toppings.forEach((item) => {
        item.disabled = !item.checked && checkedCount >= limit;
    });

    const selection = getBuilderSelection();
    document.querySelector(".builder-price").textContent = `${selection.price.toFixed(2)} €`;

}

document.querySelectorAll(".builder-options input").forEach((input) => {
    input.addEventListener("change", updateBuilder);
});

document.querySelector(".builder-add").addEventListener("click", () => {
    const limit = Number(document.querySelector('input[name="size"]:checked').dataset.count);
    const checkedCount = document.querySelectorAll(".topping-options input:checked").length;
    if (checkedCount !== limit) {
        alert(`Изберете точно ${limit} добавки за този картоф.`);
        return;
    }
    const selection = getBuilderSelection();
    const name = `${selection.name} (${selection.description})`;
    const existing = cart.find((item) => item.name === name);
    if (existing) existing.quantity += 1;
    else cart.push({ name, price: selection.price, quantity: 1 });
    renderCart();
    openCart();
});

updateBuilder();

document.querySelectorAll('input[type="tel"][name$="phone"]').forEach((input) => {
    input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, "").slice(0, 10);
    });
});

document.querySelector(".cart-button").addEventListener("click", openCart);
document.querySelector(".cart-close").addEventListener("click", closeCart);
cartOverlay.addEventListener("click", closeCart);

cartItems.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const index = Number(button.dataset.index);
    if (button.dataset.action === "plus") cart[index].quantity += 1;
    if (button.dataset.action === "minus") {
        cart[index].quantity -= 1;
        if (cart[index].quantity === 0) cart.splice(index, 1);
    }
    renderCart();
});

document.querySelectorAll('input[name="order-type"]').forEach((radio) => {
    radio.addEventListener("change", () => {
        const delivery = radio.value === "delivery";
        document.querySelector(".address-field").hidden = !delivery;
        document.querySelector(".pickup-field").hidden = delivery;
        updateEstimatedReadyTime(cart.reduce((sum, item) => sum + item.quantity, 0));
    });
});

function closeOrderSuccess() {
    const modal = document.querySelector(".order-success-modal");
    const overlay = document.querySelector(".order-success-overlay");
    modal.classList.remove("open");
    overlay.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    overlay.setAttribute("aria-hidden", "true");
}

function showOrderSuccess(orderId, orderType, payload, result) {
    const modal = document.querySelector(".order-success-modal");
    const overlay = document.querySelector(".order-success-overlay");
    const details = modal.querySelector(".order-success-details");

    modal.querySelector(".order-success-number strong").textContent = orderId;
    if (orderType === "delivery") {
        details.innerHTML = `
            <strong>Доставка до адрес</strong>
            <span>${payload.address}</span>
            <span>КартофЪ ще се свърже с <strong>${payload.customerPhone}</strong> за потвърждение.</span>
        `;
    } else {
        details.innerHTML = `
            <strong>Лично взимане</strong>
            <span>${payload.pickupLocation}</span>
            <span>Клиент: <strong>${payload.customerName}</strong></span>
            <span>Телефон: <strong>${payload.customerPhone}</strong></span>
            <span>Ще получите потвърждение за точното време за готовност.</span>
        `;
    }
    const notificationStatus = modal.querySelector(".order-notification-status");
    notificationStatus.textContent = result.notificationSent
        ? "Поръчката е изпратена автоматично към обекта."
        : "Поръчката е записана, но автоматичното известие към обекта не беше изпратено.";
    notificationStatus.classList.toggle("failed", !result.notificationSent);

    modal.classList.add("open");
    overlay.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    overlay.setAttribute("aria-hidden", "false");
    modal.querySelector(".order-success-button").focus();
}

document.querySelector(".order-success-overlay").addEventListener("click", closeOrderSuccess);
document.querySelector(".order-success-close").addEventListener("click", closeOrderSuccess);
document.querySelector(".order-success-button").addEventListener("click", closeOrderSuccess);
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeOrderSuccess();
});

checkoutButton.addEventListener("click", async () => {
    const orderType = document.querySelector('input[name="order-type"]:checked').value;
    let payload;
    if (orderType === "delivery") {
        const name = document.querySelector('[name="customer-name"]').value.trim();
        const phone = document.querySelector('[name="customer-phone"]').value.trim();
        const address = document.querySelector('[name="address"]').value.trim();
        if (!name) {
            document.querySelector('[name="customer-name"]').focus();
            return;
        }
        if (!phone) {
            document.querySelector('[name="customer-phone"]').focus();
            return;
        }
        if (!/^0\d{9}$/.test(phone)) {
            alert("Въведете телефонен номер с точно 10 цифри, започващ с 0.");
            document.querySelector('[name="customer-phone"]').focus();
            return;
        }
        if (!address) {
            document.querySelector('[name="address"]').focus();
            return;
        }
        payload = {
            orderType,
            customerName: name,
            customerPhone: phone,
            address,
            items: cart,
        };
    } else {
        const name = document.querySelector('[name="pickup-customer-name"]').value.trim();
        const phone = document.querySelector('[name="pickup-customer-phone"]').value.trim();
        const location = document.querySelector('[name="pickup-location"]').value;
        if (!name) {
            document.querySelector('[name="pickup-customer-name"]').focus();
            return;
        }
        if (!phone) {
            document.querySelector('[name="pickup-customer-phone"]').focus();
            return;
        }
        if (!/^0\d{9}$/.test(phone)) {
            alert("Въведете телефонен номер с точно 10 цифри, започващ с 0.");
            document.querySelector('[name="pickup-customer-phone"]').focus();
            return;
        }
        payload = {
            orderType,
            customerName: name,
            customerPhone: phone,
            pickupLocation: location,
            items: cart,
        };
    }

    try {
        const response = await fetch("/api/orders/create/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('[name="csrfmiddlewaretoken"]').value,
            },
            body: JSON.stringify(payload),
        });
        const responseText = await response.text();
        let result;
        try {
            result = JSON.parse(responseText);
        } catch {
            const statusMessage = `Сървърът върна неочакван отговор (HTTP ${response.status}).`;
            if (!response.ok) {
                throw new Error(`${statusMessage} Проверете дали поръчката е записана, преди да опитате отново.`);
            }
            throw new Error(`${statusMessage} Поръчката не е потвърдена.`);
        }
        if (!response.ok) throw new Error(result.error || "Възникна грешка.");

        cart = [];
        renderCart();
        closeCart();
        showOrderSuccess(result.orderId, orderType, payload, result);
    } catch (error) {
        alert(error instanceof TypeError
            ? "Неуспешна връзка със сървъра. Проверете дали поръчката е записана, преди да опитате отново."
            : error.message);
    }
});
