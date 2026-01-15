import json
import os
import time
from playwright.sync_api import sync_playwright

# --- CONFIGURAÇÕES ---
# INSIRA SEU LINK NOVO AQUI
REPORT_URL = "https://lookerstudio.google.com/s/mi_KNAkqTZc" 

# Dimensões EXATAS que você configurou no Looker Studio
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
        
        # DEFINIÇÃO DO VIEWPORT:
        # Colocamos um tamanho MAIOR que o relatório (2100x2100)
        # para garantir que não apareça barra de rolagem lateral ou inferior no print.
        context = browser.new_context(
            storage_state=state,
            viewport={'width': REPORT_WIDTH + 100, 'height': REPORT_HEIGHT + 100},
            device_scale_factor=1
        )
        
        page = context.new_page()
        # Timeout alto para garantir carregamento de dados pesados
        page.set_default_timeout(120000)
        
        print(f"Acessando: {REPORT_URL}")
        page.goto(REPORT_URL)
        
        # Espera longa inicial para renderizar os gráficos pesados
        print("Aguardando renderização completa (30s)...")
        time.sleep(30)

        # --- FASE 1: ATUALIZAÇÃO DOS DADOS ---
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
                    time.sleep(20) # Tempo extra após voltar para leitura
        except Exception as e:
            print(f"Erro no ciclo de refresh (seguindo para print): {e}")

        # --- FASE 2: LIMPEZA E ALINHAMENTO (CSS) ---
        print("Aplicando CSS para remover cabeçalhos e alinhar topo...")
        page.evaluate("""() => {
            // 1. Lista de tudo que pode aparecer no topo e atrapalhar
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

            // 2. Limpa margens do corpo da página
            document.body.style.backgroundColor = '#ffffff';
            document.body.style.margin = '0';
            document.body.style.padding = '0';
            document.body.style.overflow = 'hidden'; // Evita scrollbars duplas
            
            // 3. FORÇA BRUTA: Pega o container do relatório e cola no 0,0
            let reportContainer = document.querySelector('.ng2-canvas-container');
            if(reportContainer) {
                reportContainer.style.margin = '0';
                reportContainer.style.padding = '0';
                reportContainer.style.transform = 'none'; # Remove qualquer centralização automática
                reportContainer.style.position = 'absolute';
                reportContainer.style.top = '0px';
                reportContainer.style.left = '0px';
            }
        }""")
        time.sleep(5) # Espera o visual assentar

        # --- FASE 3: O CLIP EXATO ---
        print(f"Tirando screenshot CLIPADO em 0,0 até {REPORT_WIDTH}x{REPORT_HEIGHT}...")
        
        # Aqui está o segredo: CLIP.
        # Não importa o tamanho da tela, ele vai pegar esse retângulo exato.
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
