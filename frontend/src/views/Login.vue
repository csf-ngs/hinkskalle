<template>
  <v-container>
    <v-layout wrap>
      <v-row justify="center">
        <v-col cols="12" md="5">
          <v-tabs v-model="localState.tab">
            <v-tab>Login</v-tab>
            <v-tab v-if="registerEnabled">Create Account</v-tab>
          </v-tabs>
          <v-tabs-items v-model="localState.tab">
            <v-tab-item>
              <v-card flat>
                <v-card-subtitle>
                  (use your Forskalle account)
                </v-card-subtitle>
                <v-form v-model="localState.canSubmit" @submit.prevent="doLogin()">
                  <v-text-field outlined 
                    id="username" 
                    @blur="requestSignin()" 
                    v-model="localState.user.username" 
                    :rules="rules" 
                    prepend-icon="mdi-account" 
                    name="Username" 
                    label="Username" 
                    required></v-text-field>
                  <v-text-field v-if="!localState.webauthnAvailable" outlined 
                    id="password" 
                    v-model="localState.user.password" 
                    :rules="rules" 
                    prepend-icon="mdi-lock" 
                    name="Password" 
                    label="Password" 
                    type="password" 
                    required></v-text-field>
                  <v-text-field v-else disabled 
                    label="Please use your security key"
                    prepend-icon="mdi-lock"
                    ></v-text-field>
                  
                  <v-alert v-if="localState.loginError" type="error" text>
                    {{localState.loginError}}
                  </v-alert>
                  <v-card-actions>
                    <v-btn type="submit" id="login" primary large block :loading="loading" :disabled="!localState.canSubmit">Login</v-btn>
                  </v-card-actions>
                </v-form>
              </v-card>
            </v-tab-item>
            <v-tab-item>
              <v-card flat>
                <v-form v-model="localState.canRegister" @submit.prevent="doRegister()">
                  <v-row dense>
                    <v-col cols="12" md="6">
                      <hsk-text-input id="firstname" 
                        label="Firstname"
                        field="firstname"
                        :obj="localState.newUser"
                        required
                        @updated="localState.newUser=$event"></hsk-text-input>
                    </v-col>
                    <v-col cols="12" md="6">
                      <hsk-text-input id="lastname" 
                        label="Lastname"
                        field="lastname"
                        :obj="localState.newUser"
                        required
                        @updated="localState.newUser=$event"></hsk-text-input>
                    </v-col>
                    <v-col cols="12">
                      <hsk-text-input id="email" 
                        label="Email"
                        field="email"
                        :obj="localState.newUser"
                        required
                        @updated="localState.newUser=$event"></hsk-text-input>
                    </v-col>
                    <v-col cols="12">
                      <hsk-text-input id="username" 
                        label="Username"
                        field="username"
                        :obj="localState.newUser"
                        required
                        @updated="localState.newUser=$event"></hsk-text-input>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field 
                        outlined 
                        v-model="localState.password1" 
                        :type="localState.passwordVisible ? 'text': 'password'"
                        :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                        @click:append="localState.passwordVisible=!localState.passwordVisible"
                        :error="!passwordsMatching"
                        label="Password"></v-text-field>
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field 
                        outlined 
                        v-model="localState.password2" 
                        :type="localState.passwordVisible ? 'text': 'password'"
                        :append-icon="localState.passwordVisible ? 'mdi-eye' : 'mdi-eye-off'"
                        @click:append="localState.passwordVisible=!localState.passwordVisible"
                        :error="!passwordsMatching"
                        label="Repeat"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-alert v-if="localState.registerError" type="error" text>
                    {{localState.registerError}}
                  </v-alert>
                  <v-alert v-if="localState.registerSuccess" type="success" text>
                    Your account has been created - please log in now!
                  </v-alert>
                  <v-card-actions>
                    <v-btn type="submit" id="register" primary large block :loading="loading" :disabled="!localState.canRegister">Register</v-btn>
                  </v-card-actions>
                </v-form>
              </v-card>
            </v-tab-item>
          </v-tabs-items>
        </v-col>
      </v-row>
    </v-layout>
  </v-container>
</template>
<script lang="ts">
import Vue from 'vue';

import { AxiosError } from 'axios';
import { User } from '@/store/models';
import { generateMsg } from '@/store/modules/snackbar';

interface State {
  user: {
    username: string;
    password: string;
  };
  newUser: User;
  tab: number;
  canSubmit: boolean;
  loginError: string;
  canRegister: boolean;
  passwordVisible: boolean;
  password1: string;
  password2: string;
  registerSuccess: boolean;
  registerError: string;
  webauthnAvailable: boolean;
}

interface Data {
  localState: State;
  rules: Array<(val: string) => boolean | string>;
}

export default Vue.extend({
  name: 'HskLogin',
  data: (): Data => ({
    localState: {
      tab: 0,
      user: {
        username: '',
        password: '',
      },
      newUser: new User(),
      canSubmit: false,
      loginError: '',
      passwordVisible: false,
      password1: '',
      password2: '',
      canRegister: false,
      registerSuccess: false,
      registerError: '',
      webauthnAvailable: false,
    },
    rules: [
      (v: string): boolean | string => !!v || 'Required!',
    ],
  }),
  methods: {
    doRegister() {
      this.localState.registerError = '';
      this.localState.registerSuccess = false;
      this.localState.newUser.password=this.localState.password1;
      this.$store.dispatch('users/register', this.localState.newUser)
        .then(() => {
          this.localState.registerError = '';
          this.localState.registerSuccess = true;
        })
        .catch(err => {
          this.localState.registerSuccess = false;
          this.localState.registerError = generateMsg(err);
        });
    },
    doLogin() {
      this.$store.dispatch('requestAuth', this.localState.user)
        .then(() => {
          if (this.$store.getters['currentUser'].isAdmin) {
            this.$store.dispatch('adm/ldapStatus', { reload: true });
          }
          this.$router.push('/');
        })
        .catch((err: AxiosError) => {
          this.localState.loginError = generateMsg(err);
        });
    },
    requestSignin() {
      if (!this.localState.user.username) return;
      this.$store.dispatch('requestSignin', this.localState.user.username)
        .then((opts) => {
          this.localState.webauthnAvailable = opts.allowCredentials !== undefined && opts.allowCredentials.length > 0;
          if (this.localState.webauthnAvailable) {
            navigator.credentials.get({ publicKey: opts })
              .then(creds => {
                this.$store.dispatch('doSignin', creds);
              });
          }
        });
    }
  },
  computed: {
    loading(): boolean {
      return this.$store.getters.authStatus === 'loading';
    },
    registerEnabled(): boolean {
      return this.$store.getters.config.enable_register as boolean
    },
    passwordsMatching(): boolean {
      return this.localState.password1 != '' && this.localState.password2 != '' &&
        this.localState.password1 === this.localState.password2;
    },
  }
});
</script>