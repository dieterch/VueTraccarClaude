<script setup lang="ts">
import { ref, defineEmits, defineProps , onMounted } from 'vue';
import { MdEditor } from 'md-editor-v3';
import type { ExposeParam } from 'md-editor-v3';
import 'md-editor-v3/lib/style.css';

const editorRef = ref<ExposeParam>();

const props = defineProps({ content: String ,dialog: Boolean, file: String})
const emit = defineEmits(['dialog','saveContent'])


const ldialog = ref(props.dialog)
const text = ref(props.content);
// const handleUpload = (file) => {
//   console.log(file)
//   return 'https://i.postimg.cc/52qCzTVw/pngwing-com.png'
// }

const update_dialog = () => {
    // console.log('update', ldialog.value)
    emit('dialog', ldialog.value);
}
const update_content = () => {
    // console.log('update', ldialog.value)
    emit('dialog', ldialog.value);
    emit('saveContent', {'key':props.file, 'doc': text.value});
}

onMounted(() => {
    editorRef.value?.togglePreview(false);
})
</script>

<template>
    <v-dialog
        v-model="ldialog"
        width="auto"
        :min-height="600"
        >
        <v-card>
        <!--v-card-title>
            Markdown Editor
        </v-card-title-->
        <v-card-text>
            <MdEditor
            ref="editorRef"
            language="en-US"
            v-model="text"
        />
        </v-card-text>
        <v-card-actions>
            <v-btn
            color="primary"
            variant="text"
            @click="ldialog = false; update_dialog()"
            >
            Schliessen
            </v-btn>
            <v-btn
            color="primary"
            variant="text"
            @click="ldialog = false; update_content()"
            >
            Speichern
            </v-btn>
        </v-card-actions>
        </v-card>
    </v-dialog>
</template>
