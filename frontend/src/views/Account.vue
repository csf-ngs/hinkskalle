<template>
  <div class="account">
    <v-container>
      <v-row justify="center">
        <v-col cols="6">
          <h1 class="display-1 text-center">Account</h1>
        </v-col>
      </v-row>
      <v-row v-if="localState.editUser">
        <v-col cols="12" md="8" offset-md="2">
          <v-form>
            <v-container>
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field id="firstname" v-model="localState.editUser.firstname" label="Firstname" required></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field id="lastname" v-model="localState.editUser.lastname" label="Lastname" required></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field id="username" v-model="localState.editUser.username" label="Username" required></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field id="email" v-model="localState.editUser.email" label="Email" required></v-text-field>
                </v-col>
              </v-row>
              <v-row>
                <v-col cols="12">
                  <v-btn type="reset" color="warning" class="mr-4" @click.prevent="reset()">Reset</v-btn>
                  <v-btn type="submit" color="success" class="mr-4" @click="update()">Save</v-btn>
                </v-col>
              </v-row>
            </v-container>
          </v-form>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { User } from '../store/models';

import { clone as _clone } from 'lodash';

interface State {
  editUser: User | null;
}

export default Vue.extend({
  name: 'Account',
  data: (): { localState: State } => ({
    localState: {
      editUser: null,
    },
  }),
  mounted: function() {
    this.localState.editUser = _clone(this.$store.getters.currentUser);
  },
  methods: {
    reset() {
      this.localState.editUser = _clone(this.$store.getters.currentUser);
    },
  }
});
</script>