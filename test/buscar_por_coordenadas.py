"""
Script interactivo para buscar texto en coordenadas específicas del PDF.
Permite ingresar coordenadas manualmente y ver qué texto se encuentra en esa área.
También genera una imagen mostrando el área buscada.

Uso: python test\\buscar_por_coordenadas.py <ruta_pdf>
"""
import sys
import pdfplumber
from pathlib import Path
from PIL import ImageDraw, ImageFont


def dibujar_area_en_imagen(pagina, x0, y0, x1, y1, nombre_salida="test/area_busqueda.png"):
    """
    Genera una imagen del PDF con el área de búsqueda resaltada.
    
    Args:
        pagina: Página de pdfplumber
        x0, y0, x1, y1: Coordenadas del área a resaltar
        nombre_salida: Ruta donde guardar la imagen
    """
    try:
        # Convertir página a imagen
        im = pagina.to_image(resolution=150)
        pil_img = im.original
        draw = ImageDraw.Draw(pil_img, 'RGBA')
        
        # Escala para convertir coordenadas PDF a imagen
        escala = 150 / 72
        
        # Convertir coordenadas
        img_x0 = x0 * escala
        img_y0 = y0 * escala
        img_x1 = x1 * escala
        img_y1 = y1 * escala
        
        # Dibujar rectángulo del área de búsqueda
        # Relleno semi-transparente rojo
        draw.rectangle([img_x0, img_y0, img_x1, img_y1], 
                      fill=(255, 0, 0, 80), 
                      outline='red', 
                      width=3)
        
        # Agregar etiquetas con las coordenadas
        try:
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        # Dibujar coordenadas en las esquinas
        texto_coords = f"({x0:.1f}, {y0:.1f})"
        draw.text((img_x0, img_y0 - 15), texto_coords, fill='red', font=font)
        
        texto_coords2 = f"({x1:.1f}, {y1:.1f})"
        draw.text((img_x1 - 80, img_y1 + 5), texto_coords2, fill='red', font=font)
        
        # Guardar imagen
        Path(nombre_salida).parent.mkdir(parents=True, exist_ok=True)
        pil_img.save(nombre_salida, 'PNG')
        
        print(f"\n🖼️  Imagen guardada en: {nombre_salida}")
        return True
        
    except ImportError:
        print("\n⚠️  No se pudo generar la imagen (falta Pillow)")
        return False
    except Exception as e:
        print(f"\n⚠️  Error al generar imagen: {str(e)}")
        return False


def buscar_en_area(pagina, x0, y0, x1, y1):
    """
    Busca todas las palabras dentro del área especificada.
    
    Args:
        pagina: Página de pdfplumber
        x0, y0, x1, y1: Coordenadas del área a buscar
    
    Returns:
        Lista de palabras encontradas en el área
    """
    palabras = pagina.extract_words()
    palabras_en_area = []
    
    for palabra in palabras:
        # Verificar si la palabra está dentro del área
        if (palabra['x0'] >= x0 and palabra['x1'] <= x1 and
            palabra['top'] >= y0 and palabra['bottom'] <= y1):
            palabras_en_area.append(palabra)
    
    return palabras_en_area


def buscar_por_etiqueta_y_offsets(pagina, etiqueta, offset_x0, offset_y0, offset_x1, offset_y1):
    """
    Busca una etiqueta y define un área usando offsets desde esa etiqueta.
    
    Args:
        pagina: Página de pdfplumber
        etiqueta: Texto a buscar como referencia
        offset_x0, offset_y0, offset_x1, offset_y1: Offsets desde la etiqueta
    
    Returns:
        Coordenadas del área y palabras encontradas
    """
    palabras = pagina.extract_words()
    
    # Buscar la etiqueta
    for palabra in palabras:
        if etiqueta.lower() in palabra['text'].lower():
            # Calcular el área de búsqueda
            x0 = palabra['x0'] + offset_x0
            y0 = palabra['bottom'] + offset_y0
            x1 = palabra['x0'] + offset_x1
            y1 = palabra['bottom'] + offset_y1
            
            print(f"\n✓ Etiqueta '{etiqueta}' encontrada en:")
            print(f"  x0={palabra['x0']:.1f}, y0={palabra['top']:.1f}, x1={palabra['x1']:.1f}, y1={palabra['bottom']:.1f}")
            print(f"\nÁrea de búsqueda calculada:")
            print(f"  x0={x0:.1f}, y0={y0:.1f}, x1={x1:.1f}, y1={y1:.1f}")
            
            # Buscar palabras en el área
            palabras_encontradas = buscar_en_area(pagina, x0, y0, x1, y1)
            
            return (x0, y0, x1, y1), palabras_encontradas
    
    return None, []


def modo_interactivo(ruta_pdf):
    """Modo interactivo para buscar texto en el PDF."""
    
    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            if len(pdf.pages) == 0:
                print("❌ El PDF no contiene páginas.")
                return
            
            pagina = pdf.pages[0]
            
            print("=" * 80)
            print("BUSCADOR INTERACTIVO DE TEXTO EN PDF")
            print("=" * 80)
            print(f"\n📄 Dimensiones de la página: {pagina.width:.1f} x {pagina.height:.1f}")
            print("\nModos de búsqueda:")
            print("  1. Buscar por coordenadas absolutas")
            print("  2. Buscar por etiqueta + offsets")
            print("  3. Mostrar todas las palabras (primeras 50)")
            print("  4. Buscar una palabra específica")
            print("  5. Salir")
            
            while True:
                print("\n" + "-" * 80)
                opcion = input("\nSelecciona una opción (1-5): ").strip()
                
                if opcion == "1":
                    # Buscar por coordenadas absolutas
                    print("\nIngresa las coordenadas del área a buscar:")
                    try:
                        x0 = float(input("  x0 (izquierda): "))
                        y0 = float(input("  y0 (arriba): "))
                        x1 = float(input("  x1 (derecha): "))
                        y1 = float(input("  y1 (abajo): "))
                        
                        # Dibujar el área en una imagen
                        dibujar_area_en_imagen(pagina, x0, y0, x1, y1)
                        
                        palabras = buscar_en_area(pagina, x0, y0, x1, y1)
                        
                        if palabras:
                            print(f"\n✓ Encontradas {len(palabras)} palabra(s) en el área:")
                            for i, palabra in enumerate(palabras, 1):
                                print(f"  {i}. '{palabra['text']}' -> "
                                      f"x0={palabra['x0']:.1f}, y0={palabra['top']:.1f}, "
                                      f"x1={palabra['x1']:.1f}, y1={palabra['bottom']:.1f}")
                            
                            # Concatenar el texto
                            texto_completo = " ".join([p['text'] for p in palabras])
                            print(f"\n📝 Texto completo: {texto_completo}")
                        else:
                            print("\n❌ No se encontraron palabras en esa área.")
                            print("   Pero puedes ver el área marcada en la imagen generada.")
                    
                    except ValueError:
                        print("❌ Error: Ingresa valores numéricos válidos.")
                
                elif opcion == "2":
                    # Buscar por etiqueta + offsets
                    etiqueta = input("\nIngresa la etiqueta a buscar: ").strip()
                    
                    if not etiqueta:
                        print("❌ Debes ingresar una etiqueta.")
                        continue
                    
                    print("\nIngresa los offsets desde la etiqueta:")
                    print("  (Los offsets son relativos a la posición de la etiqueta)")
                    try:
                        offset_x0 = float(input("  offset_x0 (desplazamiento horizontal inicio): "))
                        offset_y0 = float(input("  offset_y0 (desplazamiento vertical inicio): "))
                        offset_x1 = float(input("  offset_x1 (ancho del área): "))
                        offset_y1 = float(input("  offset_y1 (alto del área): "))
                        
                        area, palabras = buscar_por_etiqueta_y_offsets(
                            pagina, etiqueta, offset_x0, offset_y0, offset_x1, offset_y1
                        )
                        
                        if area:
                            # Dibujar el área en una imagen
                            x0, y0, x1, y1 = area
                            dibujar_area_en_imagen(pagina, x0, y0, x1, y1)
                        
                        if palabras:
                            print(f"\n✓ Encontradas {len(palabras)} palabra(s):")
                            for i, palabra in enumerate(palabras, 1):
                                print(f"  {i}. '{palabra['text']}' -> "
                                      f"x0={palabra['x0']:.1f}, y0={palabra['top']:.1f}, "
                                      f"x1={palabra['x1']:.1f}, y1={palabra['bottom']:.1f}")
                            
                            # Concatenar el texto
                            texto_completo = " ".join([p['text'] for p in palabras])
                            print(f"\n📝 Texto completo: {texto_completo}")
                        elif area:
                            print("\n❌ No se encontraron palabras en esa área.")
                            print("   Pero puedes ver el área marcada en la imagen generada.")
                        else:
                            print(f"\n❌ No se encontró la etiqueta '{etiqueta}' en el PDF.")
                    
                    except ValueError:
                        print("❌ Error: Ingresa valores numéricos válidos.")
                
                elif opcion == "3":
                    # Mostrar todas las palabras
                    palabras = pagina.extract_words()
                    print(f"\n📋 Mostrando las primeras 50 de {len(palabras)} palabras:")
                    print("-" * 80)
                    for i, palabra in enumerate(palabras[:50], 1):
                        print(f"{i:3d}. '{palabra['text']:30s}' -> "
                              f"x0={palabra['x0']:6.1f}, y0={palabra['top']:6.1f}, "
                              f"x1={palabra['x1']:6.1f}, y1={palabra['bottom']:6.1f}")
                
                elif opcion == "4":
                    # Buscar una palabra específica
                    buscar = input("\nIngresa la palabra a buscar: ").strip().lower()
                    
                    if not buscar:
                        print("❌ Debes ingresar una palabra.")
                        continue
                    
                    palabras = pagina.extract_words()
                    encontradas = [p for p in palabras if buscar in p['text'].lower()]
                    
                    if encontradas:
                        print(f"\n✓ Encontradas {len(encontradas)} coincidencia(s):")
                        for i, palabra in enumerate(encontradas, 1):
                            print(f"{i}. '{palabra['text']}' -> "
                                  f"x0={palabra['x0']:.1f}, y0={palabra['top']:.1f}, "
                                  f"x1={palabra['x1']:.1f}, y1={palabra['bottom']:.1f}")
                    else:
                        print(f"\n❌ No se encontró '{buscar}' en el PDF.")
                
                elif opcion == "5":
                    print("\n👋 ¡Hasta luego!")
                    break
                
                else:
                    print("❌ Opción inválida. Selecciona 1-5.")
    
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_pdf}'")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test\\buscar_por_coordenadas.py <ruta_pdf>")
        print("\nEjemplo:")
        print("  python test\\buscar_por_coordenadas.py factura.pdf")
        sys.exit(1)
    
    ruta_pdf = sys.argv[1]
    modo_interactivo(ruta_pdf)
