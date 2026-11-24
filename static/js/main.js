const tabs = document.querySelectorAll(".tab");
const cards = document.querySelectorAll(".menu-card");
const count = document.querySelector(".cart-count");
const cartDrawer = document.querySelector(".cart-drawer");
const cartOverlay = document.querySelector(".cart-overlay");
const cartItems = document.querySelector(".cart-items");
const cartTotal = document.querySelector(".cart-total strong");
const checkoutButton = document.querySelector(".checkout-button");
const noticeModal = document.querySelector(".notice-modal");
const noticeOverlay = document.querySelector(".notice-overlay");
let cart = [];
let noticeReturnFocus = null;

function parsePrice(value, emptyValue = null) {
    const normalized = String(value ?? "").trim().replace(",", ".");
    if (!normalized) return emptyValue;
    if (!/^\d+(?:\.\d+)?$/.test(normalized)) return null;
    const price = Number(normalized);
    return Number.isFinite(price) ? price : null;
}

function showNotice(message, title = "Обърнете внимание") {
    noticeReturnFocus = document.activeElement;
    noticeModal.querySelector("h2").textContent = title;
    noticeModal.querySelector(".notice-message").textContent = message;
    noticeModal.classList.add("open");
    noticeOverlay.classList.add("open");
    noticeModal.setAttribute("aria-hidden", "false");
    noticeOverlay.setAttribute("aria-hidden", "false");
    noticeModal.querySelector(".notice-button").focus();
}

function closeNotice() {
    noticeModal.classList.remove("open");
    noticeOverlay.classList.remove("open");
    noticeModal.setAttribute("aria-hidden", "true");
    noticeOverlay.setAttribute("aria-hidden", "true");
    if (noticeReturnFocus instanceof HTMLElement) noticeReturnFocus.focus();
}

noticeModal.querySelector(".notice-close").addEventListener("click", closeNotice);
noticeModal.querySelector(".notice-button").addEventListener("click", closeNotice);
noticeOverlay.addEventListener("click", closeNotice);
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && noticeModal.classList.contains("open")) closeNotice();
});


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
    cartTotal.textContent = Number.isFinite(total) ? `${total.toFixed(2)} €` : "—";
    checkoutButton.disabled = cart.length === 0 || !Number.isFinite(total);

    cartItems.replaceChildren();
    if (!cart.length) {
        const emptyMessage = document.createElement("p");
        emptyMessage.className = "cart-empty";
        emptyMessage.textContent = "Количката е празна.";
        cartItems.appendChild(emptyMessage);
        return;
    }

    cart.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "cart-item";
        const image = document.createElement("img");
        image.className = "cart-item-image";
        image.src = item.imageUrl;
        image.alt = item.name;
        image.loading = "lazy";
        const description = document.createElement("div");
        description.className = "cart-item-description";
        const name = document.createElement("strong");
        name.textContent = item.name;
        const price = document.createElement("span");
        price.textContent = Number.isFinite(item.price) && item.price > 0
            ? `${item.price.toFixed(2)} €`
            : "Цена невалидна";
        description.append(name, price);

        const controls = document.createElement("div");
        controls.className = "quantity-controls";
        const minus = document.createElement("button");
        minus.type = "button";
        minus.dataset.action = "minus";
        minus.dataset.index = index;
        minus.setAttribute("aria-label", "Премахни едно");
        minus.textContent = "−";
        const quantity = document.createElement("span");
        quantity.textContent = item.quantity;
        const plus = document.createElement("button");
        plus.type = "button";
        plus.dataset.action = "plus";
        plus.dataset.index = index;
        plus.setAttribute("aria-label", "Добави едно");
        plus.textContent = "+";
        controls.append(minus, quantity, plus);
        row.append(image, description, controls);
        cartItems.appendChild(row);
    });
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
        const price = parsePrice(button.dataset.price);
        const productId = Number(button.dataset.productId);
        if (!Number.isInteger(productId) || productId <= 0) {
            showNotice("Този продукт все още не е наличен за онлайн поръчка.", "Продуктът не е наличен");
            return;
        }
        if (price === null) {
            showNotice("Цената на продукта е невалидна. Моля, свържете се с нас.", "Проблем с цената");
            return;
        }
        if (price === 0) {
            showNotice("Цената и наличните варианти ще бъдат потвърдени от КартофЪ при поръчката.", "Цената се потвърждава");
            return;
        }
        const existing = cart.find((item) => item.type === "product" && item.productId === productId);
        if (existing) existing.quantity += 1;
        else cart.push({
            type: "product",
            productId,
            name,
            price,
            imageUrl: button.dataset.imageUrl,
            quantity: 1,
        });
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
    if (!size || !base) return null;
    const sizePrice = parsePrice(size.dataset.price);
    const basePrice = parsePrice(base.dataset.price);
    const toppingPrices = toppings.map((topping) => parsePrice(topping.dataset.price, 0));
    if (sizePrice === null || basePrice === null || toppingPrices.some((price) => price === null)) return null;
    const price = sizePrice + basePrice + toppingPrices.reduce((sum, toppingPrice) => sum + toppingPrice, 0);

    const names = toppings.map((topping) => topping.value);
    return {
        name: `КартофЪ по избор — ${size.value}`,
        description: `${base.value === "classic" ? "класически печен картоф" : "голям печен картоф"}${names.length ? `; ${names.join(", ")}` : ""}`,
        price,
        sizeId: Number(size.dataset.sizeId),
        base: base.value,
        toppingIds: toppings.map((topping) => Number(topping.dataset.toppingId)),
    };
}

function updateBuilder() {
    const size = document.querySelector('input[name="size"]:checked');
    const toppings = [...document.querySelectorAll(".topping-options input")];
    const addButton = document.querySelector(".builder-add");
    if (!size) {
        document.querySelector(".builder-price").textContent = "—";
        addButton.disabled = true;
        toppings.forEach((item) => { item.disabled = true; });
        return;
    }
    const limit = Number(size.dataset.count);
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
    if (!selection) {
        document.querySelector(".builder-price").textContent = "—";
        addButton.disabled = true;
        return;
    }
    document.querySelector(".builder-price").textContent = `${selection.price.toFixed(2)} €`;
    addButton.disabled = toppings.length < limit;

}

document.querySelectorAll(".builder-options input").forEach((input) => {
    input.addEventListener("change", updateBuilder);
});
updateBuilder();

document.querySelector(".builder-add").addEventListener("click", () => {
    const size = document.querySelector('input[name="size"]:checked');
    if (!size) {
        showNotice("В момента няма налични размери за персонализиран картоф.", "Картофът по избор не е наличен");
        return;
    }
    const limit = Number(size.dataset.count);
    const checkedCount = document.querySelectorAll(".topping-options input:checked").length;
    if (checkedCount !== limit) {
        const difference = Math.abs(limit - checkedCount);
        const message = checkedCount < limit
            ? `Избрали сте ${checkedCount} от нужните ${limit} добавки. Изберете още ${difference}, за да продължите.`
            : `Избрали сте ${checkedCount} добавки, а за този размер са нужни точно ${limit}. Премахнете ${difference}.`;
        showNotice(message, "Завършете избора си");
        return;
    }
    const selection = getBuilderSelection();
    if (!selection || !selection.sizeId || selection.toppingIds.some((id) => !id)) {
        showNotice("Изборът не е валиден. Обновете страницата и опитайте отново.", "Невалиден избор");
        return;
    }
    const name = `${selection.name} (${selection.description})`;
    const imageUrl = document.querySelector(".builder-options").dataset.builderImageUrl;
    const existing = cart.find((item) =>
        item.type === "builder"
        && item.sizeId === selection.sizeId
        && item.base === selection.base
        && item.toppingIds.length === selection.toppingIds.length
        && item.toppingIds.every((id) => selection.toppingIds.includes(id))
    );
    if (existing) existing.quantity += 1;
    else cart.push({
        type: "builder",
        sizeId: selection.sizeId,
        base: selection.base,
        toppingIds: selection.toppingIds,
        name,
        price: selection.price,
        imageUrl,
        quantity: 1,
    });
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
    const appendDetail = (value, strong = false) => {
        const element = document.createElement(strong ? "strong" : "span");
        element.textContent = value;
        details.appendChild(element);
    };
    details.replaceChildren();
    if (orderType === "delivery") {
        appendDetail("Доставка до адрес", true);
        appendDetail(payload.address);
        appendDetail(`КартофЪ ще се свърже с ${payload.customerPhone} за потвърждение.`);
    } else {
        appendDetail("Лично взимане", true);
        appendDetail(payload.pickupLocation);
        appendDetail(`Клиент: ${payload.customerName}`);
        appendDetail(`Телефон: ${payload.customerPhone}`);
        appendDetail("Ще получите потвърждение за точното време за готовност.");
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
            showNotice("Въведете телефонен номер с точно 10 цифри, започващ с 0.", "Проверете телефонния номер");
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
            items: cart.map(({ type, productId, sizeId, base, toppingIds, quantity }) => ({
                type, productId, sizeId, base, toppingIds, quantity,
            })),
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
            showNotice("Въведете телефонен номер с точно 10 цифри, започващ с 0.", "Проверете телефонния номер");
            document.querySelector('[name="pickup-customer-phone"]').focus();
            return;
        }
        payload = {
            orderType,
            customerName: name,
            customerPhone: phone,
            pickupLocation: location,
            items: cart.map(({ type, productId, sizeId, base, toppingIds, quantity }) => ({
                type, productId, sizeId, base, toppingIds, quantity,
            })),
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
        showNotice(error instanceof TypeError
            ? "Неуспешна връзка със сървъра. Проверете дали поръчката е записана, преди да опитате отново."
            : error.message, "Поръчката не беше изпратена");
    }
});
