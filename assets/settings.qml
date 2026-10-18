import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import RinUI
import ClassWidgets.Plugins

PluginPage {
    id: root
    pluginId: "http.lyang1273"
    title: qsTr("HTTP API")

    property int port: 8080
    property bool running: false

    Component.onCompleted: refreshState()

    Connections {
        target: backend
        function onServerStateChanged() { refreshState() }
    }

    function refreshState() {
        if (!backend) return
        port = backend.getPort()
        running = backend.isServerRunning()
        portSpinBox.value = port
    }

    function apply() {
        if (!backend) return
        const err = backend.applyPort(portSpinBox.value)
        if (err && err.length > 0) {
            RinWindow.showToast(err)
        } else {
            RinWindow.showToast(qsTr("已保存，端口 %1").arg(portSpinBox.value))
            refreshState()
        }
    }

    ColumnLayout {
        Layout.fillWidth: true
        spacing: 12

        Text {
            text: qsTr("服务器")
            typography: Typography.BodyStrong
        }

        SettingCard {
            Layout.fillWidth: true
            icon.name: running ? "ic_fluent_server_20_regular" : "ic_fluent_server_20_regular"
            title: running ? qsTr("运行中") : qsTr("已停止")
            description: qsTr("监听地址：%1").arg(backend ? backend.getBaseUrl() : "")
        }

        Text {
            text: qsTr("端口")
            typography: Typography.BodyStrong
        }

        SettingItem {
            Layout.fillWidth: true
            title: qsTr("HTTP 端口")
            description: qsTr("服务器监听的端口，修改后会自动重启服务器。")

            SpinBox {
                id: portSpinBox
                Layout.preferredWidth: 160
                from: 1
                to: 65535
                editable: true
            }
            Button {
                icon.name: "ic_fluent_arrow_sync_20_regular"
                text: qsTr("保存并重启")
                onClicked: apply()
            }
        }
    }
}
