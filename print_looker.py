import json
import os
import time
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
REPORT_URL = "https://lookerstudio.google.com/s/mi_KNAkqTZc" 
REPORT_WIDTH = 2000
REPORT_HEIGHT = 2000
# ---------------------

def run():
    print(f"--- Iniciando Print 'Corte Cirúrgico' ({REPORT_WIDTH}x{REPORT_HEIGHT}) ---")
    
    auth_json = os.environ.get("LOOKER_COOKIES")
    if not auth_json:
        raise ValueError("ERRO: O segredo LOOKER_COOKIES não foi encontrado!")

    state = json.loads(auth_json)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Viewport maior para garantir renderização do rodapé
        context = browser.new_context(
            storage_state=state,
            viewport={'width': REPORT_WIDTH + 100, 'height': REPORT_HEIGHT + 100},
            device_scale_factor=1
        )
        
        page = context.new_page()
        page.set_default_timeout(120000)
        
        print(f"Acessando: {REPORT_URL}")
        page.goto(REPORT_URL)
        
        print("Aguardando renderização completa (30s)...")
        time.sleep(30)

        # --- FASE 1: REFRESH ---
        try:
            print("Verificando botão Editar...")
            edit_btn = page.get_by_role("button", name="Editar", exact=True).or_(page.get_by_role("button", name="Edit", exact=True))
            if edit_btn.count() > 0 and edit_btn.first.is_visible():
                edit_btn.first.click()
                print("> Refresh: Entrou no Modo Edição...")
                time.sleep(15)
                
                leitura_btn = page.get_by_role("button", name="Leitura").or_(page.get_by_text("Leitura"))
                if leitura_btn.count() > 0:
                    leitura_btn.first.click()
                    print("> Refresh: Voltou para Leitura...")
                    time.sleep(20)
        except Exception as e:
            print(f"Erro no ciclo de refresh (seguindo para print): {e}")

        # --- FASE 2: LIMPEZA CSS (CORRIGIDA) ---
        print("Aplicando CSS para remover cabeçalhos e alinhar topo...")
        # AQUI ESTAVA O ERRO: O JavaScript não aceita '#' como comentário.
        page.evaluate("""() => {
            // 1. Ocultar barras do Google
            const selectors = [
                'header', 
                '.feature-content-header', 
                '.lego-report-header',
                '.page-navigation-panel',
                '#align-lens-view',
                '.lego-header',
                '.print-header'
            ];
            selectors.forEach(s => {
                let els = document.querySelectorAll(s);
                els.forEach(e => e.style.display = 'none');
            });

            // 2. Limpar o body
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.margin = '0';
            document.body.style.padding = '0';
            document.body.style.overflow = 'hidden';
            
            // 3. Forçar o container do relatório para a posição 0,0
            let reportContainer = document.querySelector('.ng2-canvas-container');
            if(reportContainer) {
                reportContainer.style.margin = '0';
                reportContainer.style.padding = '0';
                reportContainer.style.transform = 'none'; // CORRIGIDO: Era '#' aqui
                reportContainer.style.position = 'absolute';
                reportContainer.style.top = '0px';
                reportContainer.style.left = '0px';
            }
        }""")
        time.sleep(5) 

        # --- FASE 3: CLIP EXATO ---
        print(f"Tirando screenshot CLIPADO em 0,0 até {REPORT_WIDTH}x{REPORT_HEIGHT}...")
        
        page.screenshot(
            path="looker_evidence.png",
            clip={
                "x": 0,
                "y": 0,
                "width": REPORT_WIDTH,
                "height": REPORT_HEIGHT
            }
        )
        
        print("Sucesso! Imagem salva.")
        browser.close()

if __name__ == "__main__":
    run()
