<template>
  <v-container>
    <v-layout wrap>
      <v-row justify="center">
        <v-col cols="4">
          <v-card flat>
            <v-card-title primary-title>
              <h4>Login</h4>
            </v-card-title>
            <v-card-subtitle>
              (use your Forskalle account)
            </v-card-subtitle>
            <v-form v-model="state.canSubmit" @submit.prevent="doLogin()">
              <v-text-field id="username" v-model="state.user.username" :rules="rules" prepend-icon="mdi-account" name="Username" label="Username" required></v-text-field>
              <v-text-field id="password" v-model="state.user.password" :rules="rules" prepend-icon="mdi-lock" name="Password" label="Password" type="password" required></v-text-field>
              <v-alert v-if="state.loginError" type="error" text>
                {{state.loginError}}
              </v-alert>
              <v-card-actions>
                <v-btn type="submit" id="login" primary large block :loading="loading" :disabled="!state.canSubmit">Login</v-btn>
              </v-card-actions>
            </v-form>
          </v-card>
        </v-col>
      </v-row>
    </v-layout>
  </v-container>
</template>
<script lang="ts">
import Vue from 'vue';

import { AxiosError } from 'axios';

interface LocalState {
  user: {
    username: string;
    password: string;
  };
  canSubmit: boolean;
  loginError: string;
}

interface Data {
  state: LocalState;
  rules: Array<(val: string) => boolean | string>;
}

export default Vue.extend({
  name: 'Login',
  data: (): Data => ({
    state: {
      user: {
        username: '',
        password: '',
      },
      canSubmit: false,
      loginError: '',
    },
    rules: [
      (v: string): boolean | string => !!v || 'Required!',
    ],
  }),
  methods: {
    doLogin() {
      this.$store.dispatch('requestAuth', this.state.user)
        .then(() => {
          this.$router.push('/');
        })
        .catch((err: AxiosError) => {
          if (err.response) {
            this.state.loginError = err.response.data.message;
          }
          else if (err.request) {
            this.state.loginError = "Unable to reach API";
          }
          else {
            this.state.loginError = err.message;
          }
        });
    }
  },
  computed: {
    loading(): boolean {
      return this.$store.getters.authStatus === 'loading';
    },
  }
});
</script>