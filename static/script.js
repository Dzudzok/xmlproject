document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ Skrypt JS załadowany");

    const uploadForm = document.getElementById("upload-form");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const fileInput = document.getElementById("xml-file");
            const templateSelect = document.getElementById("template-select");

            if (!fileInput.files.length) {
                alert("Wybierz plik XML!");
                return;
            }

            const formData = new FormData();
            formData.append("xml-file", fileInput.files[0]);
            formData.append("template", templateSelect.value);

            // Pobranie wartości dla SHOP i SHOPITEM
            const shopTag = document.getElementById("shop-mapping")?.value?.trim();
            const shopItemTag = document.getElementById("shopitem-mapping")?.value?.trim();

            if (shopTag) formData.append("shop_tag", shopTag);
            if (shopItemTag) formData.append("shopitem_tag", shopItemTag);

            // Pobranie mapowań dla pozostałych pól
            document.querySelectorAll(".mapping-dropdown").forEach(dropdown => {
                const sourceTag = dropdown.getAttribute("data-source");
                const targetTag = dropdown.value;
                if (targetTag) {
                    formData.append(`mapping_${sourceTag}`, targetTag);
                }
            });

            try {
                const response = await fetch("/process", { method: "POST", body: formData });

                if (!response.ok) {
                    const errorData = await response.json();
                    alert("Błąd: " + errorData.error);
                    return;
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = "processed.xml";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error("Błąd pobierania pliku:", error);
                alert("Wystąpił błąd podczas pobierania pliku.");
            }
        });
    } else {
        console.error("❌ Błąd: Element 'upload-form' nie istnieje w HTML!");
    }
});



        document.getElementById("logout-btn").addEventListener("click", async () => {
        const response = await fetch("/logout", { method: "POST" });
        const result = await response.json();
    
        if (result.status === "success") {
            localStorage.removeItem("username");
            document.getElementById("welcome-message").innerText = "Witaj w procesorze XML";
            document.getElementById("logout-btn").classList.add("hidden");
        }
        });
    

        // Obsługa wyboru pliku XML
        document.getElementById("xml-file").addEventListener("change", async (event) => {
        const file = event.target.files[0];
        if (!file) return;
    
        const formData = new FormData();
        formData.append("xml-file", file);
    
        // Pobranie tagów z XML klienta
        const response = await fetch("/get-tags", { method: "POST", body: formData });
        const tags = await response.json();
    
        const mappingContainer = document.getElementById("mapping-container");
        mappingContainer.innerHTML = "";
    
        if (!Array.isArray(tags) || tags.length === 0) {
            mappingContainer.innerHTML = "<p class='text-red-500'>Błąd: Brak tagów w pliku XML.</p>";
            return;
        }
    
        // Znalezienie głównego tagu (pierwszy w pliku)
        const rootTag = tags[0]; 
        const childTags = tags.slice(1); 
    
        // Dodanie wyboru głównego tagu i tagu produktu
        const shopSelect = document.getElementById("shop-mapping");
        const shopItemSelect = document.getElementById("shopitem-mapping");
    
        shopSelect.innerHTML = tags.map(tag => `<option value="${tag}">${tag}</option>`).join("");
        shopItemSelect.innerHTML = childTags.map(tag => `<option value="${tag}">${tag}</option>`).join("");
    
        shopSelect.value = rootTag;
        shopItemSelect.value = childTags.length > 0 ? childTags[0] : rootTag;
    
        // ✅ Teraz generujemy mapowanie dla pozostałych pól
        const selectedShopItemTag = shopItemSelect.value;
        const filteredTags = tags.filter(tag => tag !== rootTag && tag !== selectedShopItemTag);
    
        filteredTags.forEach(tag => {
            const div = document.createElement("div");
            div.innerHTML = `<label>${tag}</label> 
                <select class="mapping-dropdown" data-source="${tag}">
                    <option value="">-- Wybierz pole --</option>
                </select>`;
            mappingContainer.appendChild(div);
        });
    
        // Pobranie szablonu do mapowania
        const template = document.getElementById("template-select").value;
        const templateData = await fetch("/get-mapping", {
            method: "POST",
            body: new URLSearchParams({ template })
        }).then(res => res.json());
    
        if (!templateData || templateData.error) {
            mappingContainer.innerHTML += "<p class='text-red-500'>Błąd: Nie można pobrać mapowania dla wybranego szablonu.</p>";
            return;
        }
    
        // Dodanie opcji do rozwijanych list
        document.querySelectorAll(".mapping-dropdown").forEach(dropdown => {
            Object.entries(templateData).forEach(([key, value]) => {
                const option = document.createElement("option");
                option.value = key;
                option.textContent = value;
                dropdown.appendChild(option);
            });
        });
    });
    
    
    
    
    
    
        // Dodanie opcji do rozwijanej listy
        document.querySelectorAll(".mapping-dropdown").forEach(dropdown => {
            Object.entries(templateData).forEach(([key, value]) => {
                const option = document.createElement("option");
                option.value = key;
                option.textContent = value;
                dropdown.appendChild(option);
            });
        });
  
    

    
    document.getElementById("save-mapping").addEventListener("click", async () => {
        const template = document.getElementById("template-select").value;
        const mapping = {};
    
        document.querySelectorAll(".mapping-dropdown").forEach(dropdown => {
            const sourceTag = dropdown.getAttribute("data-source");
            const targetTag = dropdown.value;
            if (targetTag) {
                mapping[targetTag] = sourceTag;
            }
        });
    
        // Pobranie wartości dla SHOP i SHOPITEM
        document.querySelectorAll(".mapping-input").forEach(input => {
            const sourceTag = input.getAttribute("data-source");
            const newTagName = input.value.trim();
            if (newTagName) {
                mapping[sourceTag] = newTagName;
            }
        });
    
        const response = await fetch("/set-mapping", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ template, mapping })
        });
    
        const result = await response.json();
        alert(result.message);
    });
    
    
    
    
    
    document.getElementById("upload-form").addEventListener("submit", async (event) => {
        event.preventDefault();
    
        const fileInput = document.getElementById("xml-file");
        const templateSelect = document.getElementById("template-select");
    
        if (!fileInput.files.length) {
            alert("Wybierz plik XML!");
            return;
        }
    
        const formData = new FormData();
        formData.append("xml-file", fileInput.files[0]);
        formData.append("template", templateSelect.value);
    
        // Pobranie wartości dla SHOP i SHOPITEM
        const shopTag = document.getElementById("shop-mapping").value.trim();
        const shopItemTag = document.getElementById("shopitem-mapping").value.trim();
    
        if (shopTag) formData.append("shop_tag", shopTag);
        if (shopItemTag) formData.append("shopitem_tag", shopItemTag);
    
        // Pobranie mapowań dla pozostałych pól
        document.querySelectorAll(".mapping-dropdown").forEach(dropdown => {
            const sourceTag = dropdown.getAttribute("data-source");
            const targetTag = dropdown.value;
            if (targetTag) {
                formData.append(`mapping_${sourceTag}`, targetTag);
            }
        });
    
        try {
            const response = await fetch("/process", { method: "POST", body: formData });
    
            if (!response.ok) {
                const errorData = await response.json();
                alert("Błąd: " + errorData.error);
                return;
            }
    
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = "processed.xml";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Błąd pobierania pliku:", error);
            alert("Wystąpił błąd podczas pobierania pliku.");
        }
    });
    
    
