const { Client, LocalAuth } = require('whatsapp-web.js');
const mqtt = require('mqtt');
const qrcode = require('qrcode-terminal');

console.log(":rocket: Iniciando bot WhatsApp...");

// ===== CONFIG =====
const MEU_GRUPO = '120363404949211837@g.us';

const MQTT_BROKER_HOST = '192.168.56.101';
const MQTT_BROKER_PORT = 1883;
const MQTT_USER = 'joao_marcelo123';
const MQTT_PASSWORD = 'Joao@homesouza';

const TOPICO_ALERTA = 'trabalho/alerta';

const TOPICO_COMANDO = 'trabalho/comando';


const client = new Client({
    authStrategy: new LocalAuth()
});

client.on('qr', qr => {
    qrcode.generate(qr, { small: true });
    console.log(':white_check_mark: Escaneie o QR Code no WhatsApp');
});

client.on('ready', () => {
    console.log(':white_check_mark: WhatsApp conectado com sucesso!');
    conectarMQTT();
});

// ===== COMANDOS VIA GRUPO =====
client.on('message_create', async (msg) => {
    try {
        console.log('--- MENSAGEM CRIADA (ENVIADA OU RECEBIDA) ---');

        
        const chatId = msg.fromMe ? msg.to : msg.from;

        
        if (chatId === MEU_GRUPO) {
            const textoOriginal = msg.body.trim();
            const texto = textoOriginal.toLowerCase();

            
            if (texto === 'status') {
                let statusMqtt = 'desconectado ❌';

                if (mqttClient && mqttClient.connected) {
                    statusMqtt = 'conectado ✅';
                }

                await msg.reply(
                    `🤖 Bot online!\n` +
                    `MQTT: ${statusMqtt}\n` +
                    `Broker: ${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`
                );
                return;
            }

        
            if (texto.startsWith('setar ') || texto.startsWith('set ')) {
                
                let valorStr;
                if (texto.startsWith('setar ')) {
                    valorStr = textoOriginal.substring(6).trim(); 
                } else {
                    valorStr = textoOriginal.substring(4).trim(); 
                }

                
                const valor = Number(valorStr.replace(',', '.'));

                if (isNaN(valor)) {
                    await msg.reply('❌ Valor inválido. Use por exemplo: "setar 25" ou "set 25"');
                    return;
                }

                if (!mqttClient || !mqttClient.connected) {
                    await msg.reply('❌ MQTT não está conectado. Tente novamente mais tarde.');
                    return;
                }

                const payload = JSON.stringify({
                    source: 'whatsapp',
                    command: 'set_temperature',
                    value: valor,
                    timestamp: new Date().toISOString()
                });

                mqttClient.publish(TOPICO_COMANDO, payload, (err) => {
                    if (err) {
                        console.error('Erro ao publicar no MQTT:', err);
                    } else {
                        console.log(`Comando publicado em ${TOPICO_COMANDO}:`, payload);
                    }
                });

                await msg.reply(`✅ Comando enviado para o Home Assistant via MQTT: temperatura alvo ${valor}°C`);
                return;
            }

            
            if (!msg.fromMe) {
                await msg.reply(
                    '👋 Comandos disponíveis:\n' +
                    '- *status* → mostra status do bot/MQTT\n' +
                    '- *setar 25* ou *set 25* → envia comando de temperatura via MQTT'
                );
            }
        }
    } catch (erro) {
        console.error('Erro ao tratar mensagem do WhatsApp:', erro);
    }
});

client.initialize();



let mqttClient;

function conectarMQTT() {
    mqttClient = mqtt.connect(
        `mqtt://${MQTT_BROKER_HOST}:${MQTT_BROKER_PORT}`,
        { username: MQTT_USER, password: MQTT_PASSWORD }
    );

    mqttClient.on('connect', () => {
        console.log(':white_check_mark: MQTT conectado');
        mqttClient.subscribe(TOPICO_ALERTA, (err) => {
            if (err) {
                console.error('Erro ao se inscrever no tópico de alerta:', err);
            } else {
                console.log(`Inscrito no tópico de alerta: ${TOPICO_ALERTA}`);
            }
        });
    });

    mqttClient.on('message', async (topic, message) => {
        if (topic !== TOPICO_ALERTA) return;

        try {
            const dados = JSON.parse(message.toString());
            const temperatura = dados.value;

            const msg =
`🚨 *ALERTA DE TEMPERATURA*
🌡 ${temperatura} °C
⚠ Limite ultrapassado`;

            await client.sendMessage(MEU_GRUPO, msg);
            console.log(':white_check_mark: Alerta enviado ao grupo');

        } catch (e) {
            console.error(':x: Erro ao processar alerta:', e.message);
        }
    });
}

