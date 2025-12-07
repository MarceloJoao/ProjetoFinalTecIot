import paho.mqtt.client as mqtt
import time
import json
import tkinter as tk

MQTT_BROKER_HOST = "192.168.56.101"
MQTT_BROKER_PORT = 1883

MQTT_USER = "joao_marcelo123"
MQTT_PASSWORD = "Joao@homesouza"

TOPICO_DADOS_SENSOR = "trabalho/temperatura"
TOPICO_SETPOINT = "trabalho/estufa/setpoint"

setpoint_atual = 30.0


root = None
slider_var = None
label_temp = None
label_setpoint = None


ultimo_setpoint_aplicado = None


def on_connect(client, userdata, flags, rc):
    """Callback para verificar a conexão MQTT."""
    if rc == 0:
        print("Conectado ao Broker MQTT com sucesso!")


        client.subscribe(TOPICO_SETPOINT)
        print(f"Assinado no tópico de setpoint: {TOPICO_SETPOINT}")
    else:
        print(f"Falha na conexão, código de resultado: {rc}")


def on_message(client, userdata, msg):
    """Callback chamado quando uma mensagem é recebida em algum tópico assinado."""
    global setpoint_atual, ultimo_setpoint_aplicado

    if msg.topic == TOPICO_SETPOINT:
        try:
            payload_str = msg.payload.decode().strip()
            novo_setpoint = float(payload_str)

            setpoint_atual = novo_setpoint
           
            ultimo_setpoint_aplicado = None

            print(f"[SETPOINT] Novo setpoint recebido do HA: {setpoint_atual} °C")

        except ValueError:
            print(f"[SETPOINT] Payload inválido recebido em {TOPICO_SETPOINT}: {msg.payload}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)


client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
client.loop_start()


def atualizar_labels():
    """Atualiza os textos das labels com base no slider e no setpoint."""
    if label_temp is not None and label_setpoint is not None and slider_var is not None:
        temp_atual = slider_var.get()
        label_temp.config(text=f"Temperatura atual (slider): {temp_atual:.1f} °C")
        label_setpoint.config(text=f"Setpoint do HA: {setpoint_atual:.1f} °C")


def on_slider_change(value):
    """Callback chamado quando o slider é movimentado."""
    atualizar_labels()
   


def publicar_temperatura_periodicamente():
    """Publica periodicamente a temperatura atual (valor do slider) no MQTT."""
    if slider_var is not None:
        temperatura = float(slider_var.get())
        payload_temperatura = json.dumps({"value": temperatura})

        client.publish(TOPICO_DADOS_SENSOR, payload_temperatura, qos=1)
        print(
            f"[PUBLISH] Temperatura: {temperatura:.1f} °C "
            f"(setpoint atual: {setpoint_atual:.1f} °C) -> {TOPICO_DADOS_SENSOR}"
        )

   
    root.after(5000, publicar_temperatura_periodicamente)


def sincronizar_setpoint_com_slider():
    """
    Sincroniza o slider com o setpoint recebido do HA.
    Se o setpoint mudar, o slider é atualizado para refletir esse valor.
    """
    global ultimo_setpoint_aplicado

    if slider_var is not None:
        if ultimo_setpoint_aplicado is None or ultimo_setpoint_aplicado != setpoint_atual:
            
            slider_var.set(setpoint_atual)
            ultimo_setpoint_aplicado = setpoint_atual
            atualizar_labels()
            print(f"[GUI] Slider atualizado para refletir setpoint do HA: {setpoint_atual:.1f} °C")

    root.after(500, sincronizar_setpoint_com_slider)


def on_close():
    """Callback chamado ao fechar a janela."""
    print("Fechando estufa gráfica...")
    client.loop_stop()
    client.disconnect()
    root.destroy()


def iniciar_interface_grafica():
    global root, slider_var, label_temp, label_setpoint, ultimo_setpoint_aplicado

    root = tk.Tk()
    root.title("Estufa - Simulador de Temperatura")

   
    slider_var = tk.DoubleVar(value=setpoint_atual)

    tk.Label(root, text="Controle de Temperatura da Estufa").pack(pady=10)

    slider = tk.Scale(
        root,
        from_=10,
        to=50,
        orient=tk.HORIZONTAL,
        resolution=0.5,
        length=400,
        label="Temperatura (°C)",
        variable=slider_var,
        command=on_slider_change
    )
    slider.pack(pady=10)

    
    label_temp = tk.Label(root, text="")
    label_temp.pack(pady=5)

    label_setpoint = tk.Label(root, text="")
    label_setpoint.pack(pady=5)

    
    btn_sair = tk.Button(root, text="Sair", command=on_close)
    btn_sair.pack(pady=10)

    
    ultimo_setpoint_aplicado = setpoint_atual
    atualizar_labels()

    
    root.after(1000, publicar_temperatura_periodicamente)

    
    root.after(500, sincronizar_setpoint_com_slider)

    
    root.protocol("WM_DELETE_WINDOW", on_close)

    
    root.mainloop()


if __name__ == '__main__':
    try:
        iniciar_interface_grafica()
    except KeyboardInterrupt:
        print("Simulador de Temperatura Parado.")
        client.loop_stop()
        client.disconnect()
