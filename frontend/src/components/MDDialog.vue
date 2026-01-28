<script setup>
import { ref, defineEmits, defineProps } from 'vue'
import { saveMDDocument  } from '@/app';
import { MdPreview, MdCatalog } from 'md-editor-v3';
import 'md-editor-v3/lib/preview.css';


const props = defineProps({ content: String, dialog: Boolean, file: String})
const emit = defineEmits(['dialog'])

const mdeditdialog = ref(false)
const ldialog = ref(props.dialog)
const text = ref(props.content);

const update = () => {
    emit('dialog', ldialog.value);
}

async function saveDocument (key, doc) {
    console.log('saveMDDocument', key, doc)
    await saveMDDocument(key, doc)
    ldialog.value = false
    update()
}


const id = 'preview-only';

</script>

<template>
    <v-dialog
        v-model="ldialog"
        width="auto"
        >
        <v-card>
        <v-card-text>
        <MdPreview
            language="en-US"
            :editorId="id" 
            :text="content"
            :modelValue="content"
            v-model="text"
        />
        <MDEditorDialog
            :content="text"
            :file="props.file"
            :dialog="mdeditdialog"
            :key="mdeditdialog" 
            @dialog="(e)=>{mdeditdialog = e}"
            @saveContent="(e)=>{saveDocument(e.key, e.doc)}"
        />
        </v-card-text>
        <v-card-actions>
            <v-btn
            color="primary"
            variant="text"
            @click="ldialog = false; update()"
            >
            Schliessen
            </v-btn>
            <v-btn
            color="tertiary"
            variant="text"
            @click="mdeditdialog=true;"
            >
            Bearbeiten
            </v-btn>
        </v-card-actions>
        </v-card>
    </v-dialog>
</template>
