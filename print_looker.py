import json
import os
import time
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
REPORT_URL = "https://lookerstudio.google.com/s/mi_KNAkqTZc"
# ---------------------

def run():
    print("--- Iniciando Print Focado no Elemento (.ng2-canvas-container) ---")
    
    auth_json = os.environ.get("LOOKER_COOKIES")
    if not auth_json:
        raise ValueError("ERRO: O segredo LOOKER_COOKIES não foi encontrado!")

    state = json.loads(auth_json)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # TRUQUE 1: Viewport Gigante
        # Definimos uma altura exagerada (4000px) para garantir que o container
        # se expanda totalmente e não tenha barra de rolagem interna cortando o fim.
        context = browser.new_context(
            storage_state=state,
            viewport={'width': 1920, 'height': 4000},
            device_scale_factor=1 # Garante que não haja zoom indesejado
        )
        
        page = context.new_page()
        page.set_default_timeout(90000)
        
        print(f"Acessando: {REPORT_URL}")
        page.goto(REPORT_URL)
        
        # Espera o container específico aparecer no DOM
        print("Aguardando carregamento do container do relatório...")
        try:
            page.wait_for_selector(".ng2-canvas-container", state="visible", timeout=60000)
        except:
            print("Aviso: Container demorou, prosseguindo mesmo assim...")
            
        time.sleep(20) # Tempo extra para os gráficos renderizarem

        # --- FASE 1: REFRESH DOS DADOS (Ciclo Editar/Leitura) ---
        try:
            print("Verificando necessidade de refresh...")
            edit_btn = page.get_by_role("button", name="Editar", exact=True).or_(page.get_by_role("button", name="Edit", exact=True))
            if edit_btn.count() > 0 and edit_btn.first.is_visible():
                edit_btn.first.click()
                print("> Modo Edição ativado (Refresh)...")
                time.sleep(15)
                
                leitura_btn = page.get_by_role("button", name="Leitura").or_(page.get_by_text("Leitura"))
                if leitura_btn.count() > 0:
                    leitura_btn.first.click()
                    print("> Voltando para Leitura...")
                    time.sleep(15)
        except Exception as e:
            print(f"Erro no ciclo de refresh (ignorado): {e}")

        # --- FASE 2: LIMPEZA DE CABEÇALHOS (CSS) ---
        # Mesmo tirando print do elemento, às vezes o cabeçalho fixo do Google atrapalha.
        # Vamos escondê-lo só por garantia.
        print("Ocultando cabeçalhos flutuantes...")
        page.evaluate("""() => {
            const selectors = [
                'header', 
                '.feature-content-header', 
                '.lego-report-header',
                '.page-navigation-panel'
            ];
            selectors.forEach(s => {
                let els = document.querySelectorAll(s);
                els.forEach(e => e.style.display = 'none');
            });
        }""")
        time.sleep(2)

        # --- FASE 3: SCREENSHOT DO ELEMENTO ESPECÍFICO ---
        print("Localizando a div '.ng2-canvas-container'...")
        
        # Encontra o elemento que você me passou
        # Usamos .first para pegar a primeira página (caso o DOM carregue outras ocultas)
        canvas_element = page.locator(".ng2-canvas-container").first
        
        if canvas_element.count() > 0:
            print("Elemento encontrado! Tirando screenshot focado...")
            
            # TRUQUE 2: Screenshot do Elemento
            # Ao chamar .screenshot() no elemento e não na page,
            # ele ignora o fundo cinza, as laterais e o topo. Salva só o retângulo.
            canvas_element.screenshot(path="looker_evidence.png")
            print("Sucesso! Imagem salva: looker_evidence.png")
        else:
            print("ERRO CRÍTICO: Não achei a div .ng2-canvas-container. Tirando print da página toda como backup.")
            page.screenshot(path="looker_evidence_backup.png", full_page=True)

        browser.close()
    
    print("--- Finalizado ---")

if __name__ == "__main__":
    run()
