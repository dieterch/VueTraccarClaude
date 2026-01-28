<template>
    <v-dialog
        width="400px"
    >
    <template v-slot:activator="{ props }">
            <v-btn
                class="d-flex"
                v-bind="props" 
                :text='ldate.toLocaleDateString("de-CA", {year:"numeric", month: "2-digit", day:"2-digit"})'
                prepend-icon="mdi-calendar-start"
                color="white"
                noblock
                noflat
                >
            </v-btn>
        </template>
        
        <template v-slot:default="{ isActive }">
            <v-card>
                <v-date-picker 
                show-adjacent-months
                class="ml-5"
                v-model="ldate"
                @update:model-value="update"
                >
                </v-date-picker>
            <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn
            text="Ok"
            @click="isActive.value = false"
            ></v-btn>
            </v-card-actions>
        </v-card>
    </template>
    </v-dialog>
</template>

<script setup>
import { ref, defineEmits, defineProps } from 'vue';

const props = defineProps(['datum']);
const emit = defineEmits(['getDate']);
//import { startdate } from '@/app';

// local state
const ldate = ref(props.datum);

// return the date to the parent component
const update = () => {
    emit('getDate', ldate.value);
}

</script>