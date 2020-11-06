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
            <v-form>
              <v-text-field v-model="state.user.username" prepend-icon="mdi-account" name="Username" label="Username" required></v-text-field>
              <v-text-field v-model="state.user.password" prepend-icon="mdi-lock" name="Password" label="Password" type="password" required></v-text-field>
              <v-card-actions>
                <v-btn primary large block @click="doLogin()" :disabled="!canSubmit">Login</v-btn>
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

interface LocalState {
  user: {
    username: string;
    password: string;
  };
}

interface Data {
  state: LocalState;
}

export default Vue.extend({
  name: 'Login',
  data: (): Data => ({
    state: {
      user: {
        username: '',
        password: '',
      }
    }
  }),
  methods: {
    doLogin() {
      console.log(this.state);
      this.$store.dispatch('requestAuth', this.state.user)
        .then((res) => {
          console.log(res);
        })
        .catch((err) => {
          console.error(err);
        });
    }
  },
  computed: {
    canSubmit(): boolean {
      return this.state.user.username !== '' && this.state.user.password !== '';
    }
  }
});
</script>