<script setup>
import { ref, defineEmits, defineProps , onMounted } from 'vue';
import { dohash, validPassword, getCookie, setCookie, deleteCookie } from "@/tools";

const dialog = ref(false);
const username = ref('');
const password = ref('');

const props = defineProps({ authenticated: Boolean, hash: String })
const emit = defineEmits(['authenticated'])
const show1 = ref(false)
const passord = ref('Password')

const login = async() => {
    //console.log('login', password.value)
    await dohash(password.value)
    if (await validPassword(password.value, props.hash )) {
        setCookie('authenticated', props.hash, 365)
        emit('authenticated', true);
    } else {
        alert('Invalid Password')
    }

}

onMounted(() => {
    let chash = getCookie('authenticated')
    if (chash === props.hash) {
        emit('authenticated', true);
    }  else {
        deleteCookie('authenticated')
    }
})
</script>

<template>
    <div 
        class="d-flex align-center justify-center"
        style="height: 100vh">
        <v-sheet width="400" class="mx-auto">
            <v-form fast-fail @submit.prevent="login">
                <!--v-text-field  variant="underlined" v-model="username" label="User Name"></v-text-field-->

                <v-text-field 
                    variant="underlined" 
                    :append-icon="show1 ? 'mdi-eye' : 'mdi-eye-off'"
                    :type="show1 ? 'text' : 'password'"
                    v-model="password" 
                    label="Password" 
                    @click:append="show1 = !show1"
                ></v-text-field>
                <!--a href="#" class="text-body-2 font-weight-regular">Forgot Password?</a-->

                <v-btn type="submit" variant="outlined" color="primary" block class="mt-2">Submit</v-btn>

            </v-form>
            <!--div class="mt-2">
                <p class="text-body-2">Don't have an account? <a href="#">Sign Up</a></p>
            </div-->
        </v-sheet>
    </div>
</template>
