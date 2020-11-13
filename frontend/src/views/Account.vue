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
                  <v-btn type="submit" color="success" class="mr-4" @click.prevent="update()">Save</v-btn>
                  <v-dialog v-model="localState.confirmDelete" persistent max-width="250px">
                    <template v-slot:activator="{ on, attrs }">
                      <v-btn disabled id="delete" color="error" v-bind="attrs" v-on="on">Delete</v-btn>
                    </template>
                    <v-card>
                      <v-card-title class="headline">Delete Account?</v-card-title>
                      <v-card-text>
                        Delete yourself and all your containers and all that you stand for?
                      </v-card-text>
                      <v-card-actions>
                        <v-spacer></v-spacer>
                        <v-btn color="success" text @click="localState.confirmDelete=false">Hold on!</v-btn>
                        <v-btn id="do-delete" color="error" text @click="deleteAccount()">Sayonara!</v-btn>
                      </v-card-actions>
                    </v-card>
                  </v-dialog>
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
  confirmDelete: boolean;
}

export default Vue.extend({
  name: 'Account',
  data: (): { localState: State } => ({
    localState: {
      editUser: null,
      confirmDelete: false,
    },
  }),
  mounted: function() {
    this.localState.editUser = _clone(this.$store.getters.currentUser);
  },
  methods: {
    reset() {
      this.localState.editUser = _clone(this.$store.getters.currentUser);
    },
    update() {
      this.$store.dispatch('users/update', this.localState.editUser)
        .then(user => {
          console.log(user);
          this.$store.commit('setUser', user);
          this.localState.editUser = _clone(this.$store.getters.currentUser);
          this.$store.commit('snackbar/showSuccess', "Hooray!");
        });
    },
    deleteAccount() {
      this.$store.dispatch('users/delete', this.localState.editUser)
        .then(() => {
          this.$store.commit('logout');
          this.$router.push('/login');
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
      this.localState.confirmDelete=false;
    },
  }
});
</script>