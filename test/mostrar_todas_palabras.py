"""
Script para visualizar TODAS las palabras detectadas por pdfplumber.
Dibuja un rectángulo alrededor de cada palabra para ver qué detecta la librería.

Ejecutar: python test\\mostrar_todas_palabras.py <ruta_pdf>
"""
import sys
from pathlib import Path

def mostrar_todas_palabras(ruta_pdf, ruta_salida="test/todas_palabras.png"):
    """Genera una imagen con TODAS las palabras detectadas marcadas."""
    try:
        import pdfplumber
        from PIL import ImageDraw, ImageFont
    except ImportError as e:
        print(f"❌ ERROR: Falta instalar dependencias")
        print(f"   {str(e)}")
        print("\nInstalar con:")
        print("   pip install pdfplumber Pillow")
        return
    
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            if len(pdf.pages) > 0:
                pagina = pdf.pages[0]
                
                print("="*80)
                print("GENERANDO IMAGEN CON TODAS LAS PALABRAS DETECTADAS")
                print("="*80)
                print(f"\n📄 Dimensiones: {pagina.width:.1f} x {pagina.height:.1f}")
                
                # Convertir la página a imagen con alta resolución
                im = pagina.to_image(resolution=150)
                pil_img = im.original
                draw = ImageDraw.Draw(pil_img, 'RGBA')
                
                # Extraer todas las palabras
                palabras = pagina.extract_words()
                print(f"🔤 Total de palabras detectadas: {len(palabras)}\n")
                
                # Escala para convertir coordenadas PDF a imagen
                escala = 150 / 72
                
                # Intentar cargar una fuente, si falla usar la default
                try:
                    font = ImageFont.truetype("arial.ttf", 8)
                except:
                    font = ImageFont.load_default()
                
                # Dibujar un rectángulo alrededor de cada palabra
                print("Dibujando palabras...")
                for i, palabra in enumerate(palabras):
                    # Coordenadas escaladas
                    x0 = palabra['x0'] * escala
                    y0 = palabra['top'] * escala
                    x1 = palabra['x1'] * escala
                    y1 = palabra['bottom'] * escala
                    
                    # Alternar colores para mejor visualización
                    if i % 4 == 0:
                        color = (255, 0, 0, 100)  # Rojo
                        outline = 'red'
                    elif i % 4 == 1:
                        color = (0, 255, 0, 100)  # Verde
                        outline = 'green'
                    elif i % 4 == 2:
                        color = (0, 0, 255, 100)  # Azul
                        outline = 'blue'
                    else:
                        color = (255, 165, 0, 100)  # Naranja
                        outline = 'orange'
                    
                    # Dibujar rectángulo con relleno semi-transparente
                    draw.rectangle([x0, y0, x1, y1], fill=color, outline=outline, width=1)
                    
                    # Dibujar número de palabra (opcional, solo para las primeras 50)
                    if i < 50:
                        draw.text((x0, y0 - 10), str(i+1), fill='black', font=font)
                
                # Guardar la imagen
                print(f"\n💾 Guardando imagen en: {ruta_salida}")
                pil_img.save(ruta_salida, 'PNG')
                
                print("\n" + "="*80)
                print(f"✅ Imagen generada exitosamente")
                print("="*80)
                
                # Mostrar las primeras 30 palabras en consola
                print("\n📋 PRIMERAS 30 PALABRAS DETECTADAS:")
                print("-" * 80)
                for i, palabra in enumerate(palabras[:300]):
                    print(f"{i+1:3d}. '{palabra['text']:30s}' "
                          f"x0={palabra['x0']:6.1f} top={palabra['top']:6.1f} "
                          f"x1={palabra['x1']:6.1f} bottom={palabra['bottom']:6.1f}")
                
                if len(palabras) > 30:
                    print(f"\n... y {len(palabras) - 30} palabras más")
                
                print("\n💡 Abre la imagen para ver todas las palabras marcadas con rectángulos de colores")
                print("   Los números indican el orden de las primeras 50 palabras detectadas")
                
            else:
                print("❌ El PDF no contiene páginas.")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test\\mostrar_todas_palabras.py <ruta_pdf> [ruta_salida]")
        print("\nEjemplo:")
        print("  python test\\mostrar_todas_palabras.py factura.pdf")
        print("  python test\\mostrar_todas_palabras.py factura.pdf test/palabras.png")
        sys.exit(1)
    
    ruta_entrada = sys.argv[1]
    ruta_salida = sys.argv[2] if len(sys.argv) > 2 else "test/todas_palabras.png"
    
    # Asegurar que el directorio existe
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    
    mostrar_todas_palabras(ruta_entrada, ruta_salida)
